# GL.iNet GL-AR300M16 — Isolated Classroom AP Setup

<div align="center">

| 🏠 [TutorBox](../../README.md) | 📚 [Docs](../../docs/README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 **Infrastructure** › **GL.iNet** › **Initial AP Setup** • **Related:** [Hardware Topology](../../docs/architecture/hardware-topology.md) • [ESP32 Clicker Transport](../../docs/architecture/esp32-clicker-transport.md)

</div>

---

Provisioning runbook for the **GL.iNet GL-AR300M16** as the isolated classroom Access Point:
broadcasting SSID `TutorBox`, serving local DHCP to student devices and ESP32 clickers, with the
**WAN path removed at four independent layers** so the appliance cannot reach the internet even if
someone plugs in a live uplink cable.

> [!WARNING]
> Every step below is performed **without internet access**. Read §2 (Recovery) *before* touching
> the WAN or firewall configuration — a mistake here locks you out of a router you cannot reach
> through the cloud.

## Table of Contents
- [1. Hardware & Addressing Plan](#1-hardware--addressing-plan)
- [2. Recovery & Safety Net (read first)](#2-recovery--safety-net-read-first)
- [3. Step 1 — First Boot & Admin Hardening](#3-step-1--first-boot--admin-hardening)
- [4. Step 2 — Wi-Fi: SSID TutorBox](#4-step-2--wi-fi-ssid-tutorbox)
- [5. Step 3 — LAN, DHCP & the Jetson Static Lease](#5-step-3--lan-dhcp--the-jetson-static-lease)
- [6. Step 4 — Kill the WAN Path (4 layers)](#6-step-4--kill-the-wan-path-4-layers)
- [7. Step 5 — Disable Cloud, Repeater & DNS Leaks](#7-step-5--disable-cloud-repeater--dns-leaks)
- [8. Step 6 — Verification Checklist](#8-step-6--verification-checklist)
- [9. Known Limitations & Field Notes](#9-known-limitations--field-notes)
- [10. Rollback](#10-rollback)

---

## <a id="1-hardware--addressing-plan"></a>1. Hardware & Addressing Plan

The GL-AR300M16 runs GL.iNet firmware on top of **OpenWrt**, so everything is configurable through
either the web UI (LuCI / GL.iNet Admin Panel) or `uci` over SSH. Relevant characteristics:

| Property | Value | Consequence for TutorBox |
| :--- | :--- | :--- |
| Radio | 2.4 GHz 802.11n only | Matches the ESP32 clickers, which are 2.4 GHz only. No 5 GHz decision to make. |
| Ethernet | 2 × 10/100 (WAN + LAN) | The Jetson takes the **LAN** port. The WAN port is decommissioned in §6. |
| Flash | 16 MB | Do not install extra packages. Everything below uses the stock image. |
| Default LAN IP | `192.168.8.1` | Admin panel at `http://192.168.8.1`. |

**Addressing plan** (defined here; the repo had no prior IP plan):

| Host | Address | Assignment |
| :--- | :--- | :--- |
| Router (gateway + DNS + DHCP) | `192.168.8.1` | Static, firmware default |
| Jetson Orin Nano (Nginx :80) | `192.168.8.2` | Static DHCP lease by MAC (§5) |
| Student devices & ESP32 clickers | `192.168.8.100 – 192.168.8.159` | DHCP pool, 60 addresses for 15–20 sessions |
| Reserved / staff laptop | `192.168.8.3 – 192.168.8.99` | Manual, outside the pool |

Students reach the PWA at **`http://192.168.8.2`** or **`http://tutorbox`** (local DNS, §5).

---

## <a id="2-recovery--safety-net-read-first"></a>2. Recovery & Safety Net (read first)

You are about to delete the router's only route to the outside world. Two escape hatches:

1. **Factory reset** — with the router powered on, hold the reset button ~10 seconds until the LED
   flashes rapidly, then release. All configuration below is erased; start again from §3.
2. **U-Boot recovery mode** — power off, hold reset, apply power, keep holding until the LED
   flashes, then release. Set your laptop to a static `192.168.1.2/24` and browse to
   `http://192.168.1.1` to re-flash firmware. This works even when the OS config is unbootable.

Before starting, **write down the Jetson's Ethernet MAC address** — §5 needs it:

```bash
# On the Jetson
ip link show eth0 | awk '/link\/ether/ {print $2}'
```

Keep one wired laptop on the LAN port through the whole procedure. Do not do this over Wi-Fi only.

---

## <a id="3-step-1--first-boot--admin-hardening"></a>3. Step 1 — First Boot & Admin Hardening

1. Connect your laptop to the router's **LAN** port. Leave the WAN port empty.
2. Browse to `http://192.168.8.1`, choose language, and set a strong **admin password**. This same
   password is the SSH `root` password.
3. **Do the firmware update now, if you intend to do one at all.** It is the only step that needs
   internet, and after §6 the router will never be online again. Verify the version under
   *System → Firmware*, then re-run this runbook from §3 if you upgrade (an upgrade without
   "keep settings" wipes config).
4. Enable SSH access, then confirm from the laptop:

```bash
ssh root@192.168.8.1
# Confirm you are on OpenWrt and note the exact interface names — do not trust the
# names in this document blindly, they vary between firmware builds:
cat /etc/openwrt_release
uci show network | grep -E "device|ifname|proto"
ip -brief link
```

Record which physical port is `wan` — usually `eth0` on this model, with `eth1` as LAN, but
**verify** with `uci get network.wan.device` (older builds: `uci get network.wan.ifname`). §6
depends on this being right.

---

## <a id="4-step-2--wi-fi-ssid-tutorbox"></a>4. Step 2 — Wi-Fi: SSID TutorBox

**Via the GL.iNet Admin Panel**: *Wireless → 2.4 GHz* → SSID `TutorBox`, security **WPA2-PSK**,
passphrase set, SSID visible, then Apply.

**Via SSH (`uci`)** — confirm the AP interface index first, since GL.iNet firmware often defines
several `wifi-iface` sections:

```sh
uci show wireless | grep -E "ssid|mode"     # find the index whose mode='ap'
```

Then, substituting the correct index for `[0]`:

```sh
uci set wireless.radio0.disabled='0'
uci set wireless.radio0.channel='6'          # 1, 6 or 11 — survey the room first
uci set wireless.radio0.htmode='HT20'        # HT20 is more robust in crowded rooms
uci set wireless.radio0.country='GT'
uci set wireless.@wifi-iface[0].mode='ap'
uci set wireless.@wifi-iface[0].ssid='TutorBox'
uci set wireless.@wifi-iface[0].encryption='psk2+ccmp'
uci set wireless.@wifi-iface[0].key='<classroom-passphrase>'
uci set wireless.@wifi-iface[0].hidden='0'
uci set wireless.@wifi-iface[0].isolate='1'
uci commit wireless
wifi reload
```

Two decisions worth understanding:

- **`psk2+ccmp` (WPA2 only), not WPA3 or mixed mode.** ESP32 clickers and older classroom tablets
  negotiate WPA2-PSK reliably; WPA3/SAE and mixed-mode transitions are a common source of silent
  join failures on exactly this hardware class.
- **`isolate='1'` (client isolation).** Students never need to talk to each other — only to the
  Jetson, which sits on the *wired* LAN and stays reachable. This blocks device-to-device traffic
  between student tablets at the AP level. Set to `'0'` only if a later milestone needs peer traffic.

---

## <a id="5-step-3--lan-dhcp--the-jetson-static-lease"></a>5. Step 3 — LAN, DHCP & the Jetson Static Lease

Size the pool for the classroom and pin the Jetson so the PWA URL never moves:

```sh
# DHCP pool: .100 through .159
uci set dhcp.lan.start='100'
uci set dhcp.lan.limit='60'
uci set dhcp.lan.leasetime='4h'

# Static lease for the Jetson (substitute the MAC recorded in §2)
uci add dhcp host
uci set dhcp.@host[-1].name='tutorbox'
uci set dhcp.@host[-1].mac='AA:BB:CC:DD:EE:FF'
uci set dhcp.@host[-1].ip='192.168.8.2'
uci commit dhcp
/etc/init.d/dnsmasq restart
```

The `name='tutorbox'` entry makes dnsmasq resolve `http://tutorbox` to `192.168.8.2` for every DHCP
client — friendlier than an IP for students typing on tablets.

**Optional catch-all DNS.** Resolving *every* domain to the Jetson means any address a student
types lands on the PWA instead of a browser error:

```sh
uci add_list dhcp.@dnsmasq[0].address='/#/192.168.8.2'
uci commit dhcp && /etc/init.d/dnsmasq restart
```

Skip this if you prefer failed lookups to look like failures.

---

## <a id="6-step-4--kill-the-wan-path-4-layers"></a>6. Step 4 — Kill the WAN Path (4 layers)

Each layer alone would mostly work. All four together mean that plugging a live internet cable into
the WAN port does nothing at all — which is the actual threat model in a school, where someone
*will* eventually plug in a cable to "fix the internet".

**Layer 1 — Disable the WAN interfaces:**

```sh
uci set network.wan.disabled='1'
uci set network.wan.auto='0'
uci -q delete network.wan6
uci commit network
```

**Layer 2 — Delete the firewall WAN zone and the `lan → wan` forwarding rule.** Section indexes are
not stable, so look them up by name rather than hardcoding `@zone[1]`:

```sh
# Remove lan -> wan forwarding
i=0
while uci -q get firewall.@forwarding[$i] >/dev/null; do
  if [ "$(uci -q get firewall.@forwarding[$i].dest)" = "wan" ]; then
    uci delete firewall.@forwarding[$i]; break
  fi
  i=$((i+1))
done

# Remove the wan zone itself
i=0
while uci -q get firewall.@zone[$i] >/dev/null; do
  if [ "$(uci -q get firewall.@zone[$i].name)" = "wan" ]; then
    uci delete firewall.@zone[$i]; break
  fi
  i=$((i+1))
done

uci commit firewall
/etc/init.d/firewall restart
```

**Layer 3 — Remove the default route source.** With `wan` disabled there is no upstream gateway,
but assert it explicitly so nothing re-learns one:

```sh
uci -q delete network.lan.gateway
uci commit network
/etc/init.d/network restart
ip route show          # expect ONLY the 192.168.8.0/24 link route, no 'default via'
```

**Layer 4 — Hold the physical port down at boot.** Substitute the device name verified in §3:

```sh
# Confirm first:
uci get network.wan.device        # e.g. eth0

# Then append to /etc/rc.local, ABOVE the trailing 'exit 0':
ip link set eth0 down
```

Finally, **label the WAN port physically** — a strip of tape over the socket with "NO USAR" stops
more incidents than any config line.

---

## <a id="7-step-5--disable-cloud-repeater--dns-leaks"></a>7. Step 5 — Disable Cloud, Repeater & DNS Leaks

GL.iNet firmware ships features that actively *seek* an internet path. Turn them all off.

1. **GoodCloud / remote management** — Admin Panel → *Applications → GoodCloud*: disable and unbind.
   Then confirm no cloud service survives a reboot:

```sh
ls /etc/init.d/ | grep -iE "cloud|ddns|gl_"
# For each cloud/ddns service found:
/etc/init.d/<service> stop
/etc/init.d/<service> disable
```

2. **Repeater / WISP mode** — the router will auto-rejoin any saved upstream Wi-Fi it can see.
   Admin Panel → *Internet → Repeater*: delete every saved network and disable auto-reconnect.
   Then disable any station-mode radio interface:

```sh
uci show wireless | grep "mode='sta'"          # note the index, if any exists
uci set wireless.@wifi-iface[<index>].disabled='1'
uci commit wireless && wifi reload
```

3. **Tethering** — disable USB/phone tethering in *Internet → Tethering* so a plugged-in phone
   cannot become an uplink.

4. **DNS leak prevention** — stop dnsmasq from ever consulting an upstream resolver:

```sh
uci set dhcp.@dnsmasq[0].noresolv='1'
uci -q delete dhcp.@dnsmasq[0].resolvfile
uci -q delete dhcp.@dnsmasq[0].server
uci commit dhcp
/etc/init.d/dnsmasq restart
```

5. **Auto-update** — disable automatic firmware/package updates so the router stops retrying
   downloads that can never succeed.

---

## <a id="8-step-6--verification-checklist"></a>8. Step 6 — Verification Checklist

Reboot the router (`reboot`), wait for the LED to settle, then confirm every line. **The WAN test
requires actually plugging a known-good live internet cable into the WAN port** — a test that
passes only because no cable is attached proves nothing.

- [ ] SSID `TutorBox` is visible and a phone joins with the WPA2 passphrase.
- [ ] The joined phone receives an address in `192.168.8.100–159`: check *Clients* in the admin panel.
- [ ] The Jetson holds `192.168.8.2`: `ip -brief addr show eth0` on the Jetson.
- [ ] From a student phone, `http://192.168.8.2` loads the PWA, and so does `http://tutorbox`.
- [ ] From the router: `ip route show` prints **no** `default via` line.
- [ ] From the router with the live uplink cable plugged into WAN: `ping -c2 8.8.8.8` fails, and
      `ip -brief link` shows the WAN device `DOWN`.
- [ ] From a student phone with that cable still attached: a public site fails to load, while the
      PWA still works.
- [ ] Backend health probe answers through the AP: `curl http://192.168.8.2/health` from a laptop
      on the classroom Wi-Fi (see [API Reference](../../docs/api-reference.md)).
- [ ] Reboot once more and re-check the last three items — this catches config that was never
      committed and rules that do not survive a power cycle.

Capture the output of `uci export network`, `uci export firewall`, `uci export wireless` and
`uci export dhcp` and commit them alongside this file once the configuration is proven, so the AP
can be rebuilt from scratch without repeating the discovery work.

---

## <a id="9-known-limitations--field-notes"></a>9. Known Limitations & Field Notes

- **Clock drift is now a real problem.** With no WAN there is no NTP, and neither the router nor a
  stock Jetson Orin Nano dev kit keeps time across a power cut without an RTC battery. TutorBox
  writes `created_at` timestamps into `sessions`, `audit_logs` and `quiz_generation_logs`; a Jetson
  that boots at epoch zero makes the teacher's weekly report incoherent and session expiry
  meaningless. **Mitigation**: fit an RTC module to the Jetson, or set the clock from the teacher's
  device at the start of each session. Do not treat this as solved by the network config.
- **Channel choice is empirical.** Channel 6 is a starting point, not an answer. Survey the actual
  classroom and move to 1 or 11 if the room is congested; a 2.4 GHz-only radio has nowhere else to hide.
- **100 Mbps ports and 802.11n are sufficient here** — the PWA is static assets plus small JSON
  votes. If the LLM ever streams audio to devices instead of the HDMI output, re-measure before
  assuming the link holds.
- **Client isolation is on**, so any future feature needing device-to-device traffic must revisit
  §4 rather than silently failing.
- **16 MB flash**: resist installing diagnostic packages. Use the built-in `logread`, `ip`, and
  `ping` instead.

---

## <a id="10-rollback"></a>10. Rollback

To restore internet access temporarily (e.g. for a firmware update), reverse the layers in order:

```sh
# Remove the rc.local line holding the port down, then:
uci set network.wan.disabled='0'
uci set network.wan.auto='1'
uci commit network
/etc/init.d/network restart
```

The firewall WAN zone and `lan → wan` forwarding deleted in §6 must be recreated (easiest through
LuCI → *Network → Firewall*), and the dnsmasq `noresolv` setting reverted. If any of this misbehaves,
factory reset per §2 is faster than debugging — **and re-run this entire runbook afterwards, because
a reset restores the WAN path.**
