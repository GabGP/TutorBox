# Automated Kit Setup (Ansible)

<div align="center">

| 🏠 [Utz'tutor](../../README.md) | 📚 [Docs](../../docs/README.md) | ⚙️ [Backend](../../backend/README.md) | 📱 [PWA](../../pwa/README.md) | 🔌 [Infra](../README.md) |
| :---: | :---: | :---: | :---: | :---: |

📍 [Infra](../README.md) › **Automated Kit Setup** • **Related:** [GL.iNet Setup](../glinet/initial.md) • [Captive Portal](../captive-portal.md) • [Hardware Topology](../../docs/architecture/hardware-topology.md)

</div>

---

Step-by-step instructions to turn a blank **Jetson Orin Nano** and a **GL.iNet GL-AR300M16** into a
working Utz'tutor kit, the same way every time. Three playbooks do the work: `jetson.yml` sets up
the Jetson, `router.yml` configures the router, and `verify.yml` checks the result.

> [!IMPORTANT]
> The install needs **internet on the Jetson** (packages, models). The classroom has none: the last
> step turns the Jetson's Wi-Fi off, and from then on the kit runs offline.

## Table of Contents
- [1. How It Works](#1-how-it-works)
- [2. What You Need](#2-what-you-need)
- [3. Step 1 — Flash the Jetson and Create the User](#3-step-1--flash-the-jetson-and-create-the-user)
- [4. Step 2 — Get the Repository and Ansible](#4-step-2--get-the-repository-and-ansible)
- [5. Step 3 — Describe the Kit (kit.yml)](#5-step-3--describe-the-kit-kityml)
- [6. Step 4 — Set Up the Jetson](#6-step-4--set-up-the-jetson)
- [7. Step 5 — Prepare the Router by Hand (once)](#7-step-5--prepare-the-router-by-hand-once)
- [8. Step 6 — Configure the Router](#8-step-6--configure-the-router)
- [9. Step 7 — Verify the Kit](#9-step-7--verify-the-kit)
- [10. Step 8 — Go Offline](#10-step-8--go-offline)
- [11. Updating a Kit Later](#11-updating-a-kit-later)
- [12. A Development Jetson](#12-a-development-jetson)
- [13. Optional — Sealing a Kit to Copy It as an Image](#13-optional--sealing-a-kit-to-copy-it-as-an-image)
- [14. What Is Not Automated](#14-what-is-not-automated)
- [15. Status and Troubleshooting](#15-status-and-troubleshooting)

---

## <a id="1-how-it-works"></a>1. How It Works

Ansible runs **on the Jetson itself** and describes the state the kit must be in. Running a
playbook twice changes nothing the second time, and `--check --diff` shows what a run would change
without changing it.

| File | What it is |
| :--- | :--- |
| [`bootstrap.sh`](bootstrap.sh) | Installs `uv` and Ansible for the current user. Run once per Jetson. |
| [`kit.example.yml`](kit.example.yml) | Template for `kit.yml`: the values of one kit, including its secrets. `kit.yml` is git-ignored. |
| [`group_vars/all.yml`](group_vars/all.yml) | Every other setting with its default: pinned versions, packages, models, addresses. |
| [`jetson.yml`](jetson.yml) | Sets up the Jetson. The parts are in [`tasks/`](tasks/), one file per part. |
| [`router.yml`](router.yml) | Sends [`../glinet/router.sh`](../glinet/router.sh) to the router over SSH and runs it. |
| [`verify.yml`](verify.yml) | Read-only checks of the Jetson and the router. |

The playbooks install files that live elsewhere in the repository, so there is one copy of each:

| Installed on the kit | Source in the repo |
| :--- | :--- |
| `/etc/nginx/sites-available/utztutor` | [`infra/nginx/utztutor.conf`](../nginx/utztutor.conf) |
| `/etc/systemd/system/utztutor-backend.service` | [`infra/systemd/utztutor-backend.service.j2`](../systemd/utztutor-backend.service.j2) |
| `/etc/systemd/system/utztutor-power.service` | [`infra/systemd/utztutor-power.service.j2`](../systemd/utztutor-power.service.j2) |
| `~/.config/systemd/user/utztutor-kiosk.service` | [`infra/kiosk/utztutor-kiosk.service`](../kiosk/utztutor-kiosk.service) |
| `/etc/firefox/policies/policies.json` | [`infra/kiosk/firefox-policies.json`](../kiosk/firefox-policies.json) |
| `/etc/dconf/db/local.d/00-utztutor-kiosk` | [`infra/kiosk/dconf-utztutor-kiosk`](../kiosk/dconf-utztutor-kiosk) |
| `<repo>/.env` | [`templates/env.j2`](templates/env.j2), filled from `kit.yml` |

The two `.service.j2` files are templates: the playbook fills in the user and the checkout path, so
the same files serve a kit in `/opt/utztutor` and a developer's checkout.

**Who builds what.** Ansible does what needs root or belongs to the operating system: packages,
nginx, systemd, the desktop. The app builds itself: the playbook calls
`python3 run.py --prepare`, which syncs the Python environment, builds the PWA, downloads the voice
models and compiles the Qwen3-TTS daemon, then exits without starting the server.

**The router is not an Ansible host.** OpenWrt has no Python, so Ansible's own modules cannot run
on it. `router.yml` pipes one shell script to the router over SSH. The script has two modes,
`verify` (list differences) and `apply` (make them), and both can be repeated safely.

---

## <a id="2-what-you-need"></a>2. What You Need

| Item | Notes |
| :--- | :--- |
| Jetson Orin Nano (8 GB) with an NVMe drive | The reference kit runs JetPack 7.2 (L4T R39.2, Ubuntu 24.04). |
| GL.iNet GL-AR300M16 | Stock GL.iNet firmware 4.3.28 (OpenWrt 22.03.4), the version in `router_firmware`. |
| Ethernet cable | Jetson to the router's **LAN** port. |
| Internet for the Jetson during the install | Its own Wi-Fi on any network with internet. The models alone are about 6 GB. |
| A screen and keyboard, or SSH to the Jetson | Only for the install. In the classroom the kit needs neither. |
| A PC with NVIDIA SDK Manager | Only to flash JetPack in Step 1. |

---

## <a id="3-step-1--flash-the-jetson-and-create-the-user"></a>3. Step 1 — Flash the Jetson and Create the User

Manual, once per Jetson.

1. Flash JetPack to the NVMe drive with NVIDIA SDK Manager. Use the same JetPack release on every
   kit; the versions pinned in [`group_vars/all.yml`](group_vars/all.yml) were taken from the
   reference kit.
2. On first boot, the setup wizard asks for a user. Create **`utztutor`**. This user runs the
   backend, owns the checkout and is the one the classroom screen logs in as.
3. Connect the Jetson's Wi-Fi to a network with internet.
4. Leave the router for later. Until [Step 6](#8-step-6--configure-the-router) the Jetson does not
   need it.

---

## <a id="4-step-2--get-the-repository-and-ansible"></a>4. Step 2 — Get the Repository and Ansible

Log in as `utztutor` and run:

```bash
sudo mkdir /opt/utztutor
sudo chown utztutor: /opt/utztutor
git clone https://github.com/GabGP/TutorBox /opt/utztutor
cd /opt/utztutor
./infra/ansible/bootstrap.sh
```

`bootstrap.sh` installs pinned versions of `uv` and `ansible-core` under `~/.local`. It does not
use `sudo`. Open a new terminal afterwards, so `~/.local/bin` is on your `PATH`, and check:

```bash
ansible --version      # ansible [core 2.19.14]
```

Every command from here on runs from the playbook folder:

```bash
cd /opt/utztutor/infra/ansible
```

---

## <a id="5-step-3--describe-the-kit-kityml"></a>5. Step 3 — Describe the Kit (kit.yml)

```bash
cp kit.example.yml kit.yml
nano kit.yml
```

| Value | Meaning |
| :--- | :--- |
| `kit_hostname` | Hostname of the Jetson. Number the kits: `utztutor-01`, `utztutor-02`. |
| `wifi_ssid` | The Wi-Fi name students see. Two kits within range of each other need different names. |
| `wifi_channel` | `1`, `6` or `11`. Survey the room; neighbouring kits take different channels. |
| `wifi_passphrase` | **Secret.** 8 to 63 characters. |
| `teacher_username`, `teacher_pin` | **Secret PIN.** The first teacher account, created when the backend starts on an empty database. |

Everything else has a default in [`group_vars/all.yml`](group_vars/all.yml). To change a default
for one kit, copy its line into `kit.yml`.

`kit.yml` is the Ansible counterpart of `.env`: `kit.example.yml` is committed, `kit.yml` is
git-ignored. **Keep a copy of each kit's `kit.yml` somewhere safe**, because it is the only place
the kit's Wi-Fi passphrase and PIN are written down outside the kit.

> [!NOTE]
> To keep kit files in git instead, encrypt them: `ansible-vault encrypt kit.yml` and add
> `--ask-vault-pass` to every `ansible-playbook` command. The playbooks need no change. Committing
> a vault-encrypted file is normal Ansible practice; its safety is the vault password, which must
> then be stored outside the repository.

---

## <a id="6-step-4--set-up-the-jetson"></a>6. Step 4 — Set Up the Jetson

```bash
ansible-playbook jetson.yml -K
```

`-K` asks for the `sudo` password of `utztutor`. To see what a run would change without changing
anything, add `--check --diff`. That is most useful on a kit that is already set up: on a blank
Jetson almost everything is still to be installed, so a check run can only list the first steps.

The first run takes a while: it downloads the models (about 6 GB) and compiles the Qwen3-TTS
daemon. What it does, in order:

| Part (`--tags`) | What it does |
| :--- | :--- |
| `system` | Hostname, time zone. Disables three base-image units that fail on every boot (`dnsmasq`, `isc-dhcp-server`, `isc-dhcp-server6`). |
| `packages` | `nginx-light`, `espeak-ng`, `git`, `build-essential`. |
| `cuda` | The CUDA compiler (`cuda-minimal-build-13-2`, `libcublas-dev-13-2`). The base image has the CUDA runtime only. |
| `tools` | Checks `uv`; installs Node.js and pnpm under `~/.local`, at the pinned versions. |
| `ollama` | Installs Ollama at the pinned version, starts `ollama.service`, pulls the quiz and tutor models. |
| `app` | Writes `<repo>/.env`, then runs `run.py --prepare --download-models all --build-llama --require-cuda`. |
| `nginx` | Installs and enables the site, removes Ubuntu's default site. |
| `services` | Installs, enables and starts `utztutor-backend` and `utztutor-power`. |
| `kiosk` | Automatic login, a desktop that never blanks or locks, Firefox policies, and the classroom-screen unit. |
| `network` | Stops the wired connection from using the router's DNS ([Captive Portal §6](../captive-portal.md#6-limitations--field-notes)). |

**Watching a long task.** Ansible prints the title of a task, then nothing until the task ends. The
long tasks write their output to a file in `<repo>/.cache/logs/` (git-ignored; the `log_dir`
setting), and their titles end with the file to follow. Open a second terminal on the Jetson, or a
second SSH session, and run:

```bash
tail -F /opt/utztutor/.cache/logs/prepare.log
```

`-F` (capital) waits for a file that does not exist yet and keeps following when the file is
overwritten. On a [development Jetson](#12-a-development-jetson), replace `/opt/utztutor` with your
checkout.

| Task | File to follow | What is in it |
| :--- | :--- | :--- |
| Ollama install | `.cache/logs/ollama-install.log` | The Ollama install. Overwritten each time the task runs. |
| Model downloads | `.cache/logs/ollama-pull.log` | One file for all models, appended, with a header line per model. It holds Ollama's progress display, so read it with `tail`, not an editor. |
| `run.py --prepare` | `.cache/logs/prepare.log` | Python environment, voice model downloads, the Qwen3-TTS daemon build (the longest), the PWA build. Overwritten each time the task runs. |
| Package installs (`packages`, `cuda`) | `/var/log/apt/term.log` | Written by Ubuntu, not by the playbook. Readable by the `adm` group, which the default user is in. |

A task writes its log only when it runs: on a second run where nothing needs doing, the task is
skipped and the old log stays. For everything else, `journalctl -f` shows each Ansible task as it
starts, system-wide. Adding `-v` to `ansible-playbook` prints each task's result after it ends; it
is not live.

When the run ends, **reboot once** (`sudo reboot`). The automatic login and the classroom screen
start with the next desktop session: the Jetson should boot straight to `/pantalla/` in full screen.

Good to know:

- **One part only:** `ansible-playbook jetson.yml -K --tags nginx`.
- **The build runs only when needed.** The `app` part runs `run.py --prepare` when the checkout or
  the build options changed since the last build. To force it: `-e force_prepare=true`.
- **GPU build of the voice daemon.** With `tts_cuda: true` (the default) the build fails if it
  cannot use CUDA, instead of quietly building for the CPU.
- **Four units keep the kit running:** `nginx`, `utztutor-backend` (restarts on failure),
  `utztutor-power` and `ollama` (restarts always). The classroom screen is a fifth, in the user's
  session: systemd restarts Firefox if it closes.

---

## <a id="7-step-5--prepare-the-router-by-hand-once"></a>7. Step 5 — Prepare the Router by Hand (once)

A few things on the router cannot be scripted, or must be done before a script can reach it. Read
[GL.iNet Setup §2 (Recovery)](../glinet/initial.md#2-recovery--safety-net-read-first) first.

1. Cable the Jetson to the router's **LAN** port. Leave the WAN port empty.
2. Browse to `http://192.168.8.1`, choose a language and set the **admin password**
   ([GL.iNet Setup §3](../glinet/initial.md#3-step-1--first-boot--admin-hardening)). Check the
   firmware under *System → Firmware*: it must be `router_firmware` from
   [`group_vars/all.yml`](group_vars/all.yml). Update it now if needed: after Step 6 the router is
   never online again.
3. In the admin panel, do the items the script cannot do
   ([GL.iNet Setup §7](../glinet/initial.md#7-step-5--disable-cloud-repeater--dns-leaks)):
   unbind **GoodCloud**, delete saved **Repeater** networks, turn off **Tethering** and
   **automatic updates**.
4. Give the Jetson an SSH key on the router. On the Jetson:

```bash
[ -f ~/.ssh/id_ed25519 ] || ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519
ssh root@192.168.8.1 "cat >> /etc/dropbear/authorized_keys" < ~/.ssh/id_ed25519.pub   # asks for the admin password
ssh -o BatchMode=yes root@192.168.8.1 true && echo "key works"
```

---

## <a id="8-step-6--configure-the-router"></a>8. Step 6 — Configure the Router

List the differences between the router and this kit's values. Nothing is modified:

```bash
ansible-playbook router.yml --check
```

Each `DRIFT` line is one setting that would change. Then apply:

```bash
ansible-playbook router.yml
```

It applies the settings, waits for the router, and checks again; it stops with an error if anything
still differs. No `sudo` is needed: the work happens on the router, over SSH.

It also checks the router's firmware against `router_firmware`, but never installs one: a different
version is a `DRIFT` line, and after applying it stops the run. While the Jetson is online, it asks
GL.iNet's firmware API whether a stable release newer than `router_firmware` exists for
`router_model` and prints `NEWER STABLE FIRMWARE: ...` if so. Offline, it says it could not check.
To move to a new release: update the router by hand
([GL.iNet Setup §3](../glinet/initial.md#3-step-1--first-boot--admin-hardening)), then
`router_firmware`.

| What it sets | Runbook section |
| :--- | :--- |
| Firmware version (checked only) | [§3](../glinet/initial.md#3-step-1--first-boot--admin-hardening) |
| Wi-Fi: SSID, WPA2 passphrase, channel, country, HT20, client isolation | [§4](../glinet/initial.md#4-step-2--wi-fi-ssid-utztutor) |
| DHCP pool, the Jetson's static lease (MAC read from the Jetson), catch-all DNS | [§5](../glinet/initial.md#5-step-3--lan-dhcp--the-jetson-static-lease) |
| WAN kill: interface disabled, firewall zone and forwardings removed, port held down at boot | [§6](../glinet/initial.md#6-step-4--kill-the-wan-path-4-layers) |
| `gl-cloud` and `gl_ddns` stopped and disabled, no upstream DNS | [§7](../glinet/initial.md#7-step-5--disable-cloud-repeater--dns-leaks) |

> [!WARNING]
> Applying **reloads the radio**: every phone and clicker is disconnected and must rejoin, and when
> the SSID or passphrase changed, they must be given the new one. Do it between classes. If the
> router stops answering afterwards, use the recovery steps in
> [GL.iNet Setup §2](../glinet/initial.md#2-recovery--safety-net-read-first).

Two things remain for a person: put a **"NO USAR" label on the WAN port**, and run the live-cable
test in [GL.iNet Setup §8](../glinet/initial.md#8-step-6--verification-checklist). A WAN test that
passes only because no cable is attached proves nothing.

---

## <a id="9-step-7--verify-the-kit"></a>9. Step 7 — Verify the Kit

```bash
ansible-playbook verify.yml
```

Read-only, no `sudo`, no internet. Every check runs even after one fails; the last task lists the
checks that failed. It checks that:

- `nginx`, `utztutor-backend`, `utztutor-power` and `ollama` are running and enabled, and no unit is
  in the failed state. `nvpmodel` is allowed to be (`known_failed_units`): it fails at boot on this
  board, and `utztutor-power` applies the 25W clock caps in its place.
- The 25W clock caps are the ones the kernel reports.
- The installed nginx site and units are the ones in the repository.
- `http://localhost/health` answers, a captive-portal probe is redirected to
  `http://<dns_name>/alumno/`, and an unknown API path on a foreign name stays a `404`.
- Ollama has the kit's models, the PWA is built, the voice models are present and the Qwen3-TTS
  daemon is a GPU build.
- The Jetson holds `192.168.8.2` and does not take DNS from the router.
- The router answers every name with the Jetson's address, and its settings and firmware match
  `kit.yml` and `router_firmware`.
- The classroom-screen files are installed and the user is logged in at boot.

Then the checks only a person can do: join the Wi-Fi with an iPhone and an Android phone and see
the student page open by itself ([Captive Portal §7](../captive-portal.md#7-verification)).

---

## <a id="10-step-8--go-offline"></a>10. Step 8 — Go Offline

When everything passes, turn the Jetson's own Wi-Fi off. Its Wi-Fi and Bluetooth share one radio,
and the kit is wired to the router:

```bash
ansible-playbook jetson.yml -K --tags offline
```

Then add `expect_offline: true` to `kit.yml`, so `verify.yml` also checks that the Wi-Fi stays off.
To bring the Jetson online again for an update: `sudo nmcli radio wifi on`.

---

## <a id="11-updating-a-kit-later"></a>11. Updating a Kit Later

```bash
sudo nmcli radio wifi on            # only if the update needs to download something
cd /opt/utztutor && git pull
cd infra/ansible
ansible-playbook jetson.yml --check --diff -K
ansible-playbook jetson.yml -K
ansible-playbook router.yml --check
ansible-playbook verify.yml
ansible-playbook jetson.yml -K --tags offline
```

A run downloads only what is missing. On a kit that is already complete, an update that changes
code but no dependencies works without internet.

---

## <a id="12-a-development-jetson"></a>12. A Development Jetson

The playbooks also run on a developer's Jetson, with any user and any checkout path: both are
taken from who runs the playbook and where the repository is. In `kit.yml`:

```yaml
kit_hostname: my-jetson
manage_env: false       # keep the .env you wrote by hand
kiosk_enabled: false    # keep a normal desktop: no automatic login, no full-screen browser
```

---

## <a id="13-optional--sealing-a-kit-to-copy-it-as-an-image"></a>13. Optional — Sealing a Kit to Copy It as an Image

Not implemented; this is the outline for when building every kit from the internet becomes too
slow. The playbooks stay the source of truth: an image is a finished kit, copied.

1. Build one kit with Steps 1 to 7, but do **not** go offline yet.
2. **Seal it**, so nothing that belongs to one kit ends up in the image. A future `seal.yml` would
   remove:

| Per-kit state | Where |
| :--- | :--- |
| The kit's values and secrets | `infra/ansible/kit.yml`, `<repo>/.env` |
| The database (students, sessions) | `<repo>/.cache/db/` |
| Saved Wi-Fi networks and their passwords | `nmcli connection delete <name>` for each Wi-Fi profile |
| SSH identity | `/etc/ssh/ssh_host_*` (regenerate with `ssh-keygen -A` on first boot), `~/.ssh/` |
| Machine identity | `/etc/machine-id` (empty it), the hostname |
| History | shell history, `journalctl --vacuum-time=1s`, `<repo>/.cache/logs/` |

3. Capture the NVMe drive with NVIDIA's backup tooling from a Linux PC, with the Jetson in recovery
   mode, and flash the image to each new Jetson.
4. On each new kit, without internet: write its `kit.yml`, then run `jetson.yml`, the router steps
   (5 and 6), `verify.yml` and the offline step. Every download is already in the image, so the run
   only sets what is the kit's own: hostname, `.env`, and the router with this Jetson's MAC.

The router is not imaged. `router.yml` takes under a minute and needs the Jetson's MAC anyway.

---

## <a id="14-what-is-not-automated"></a>14. What Is Not Automated

| Item | Why | Where |
| :--- | :--- | :--- |
| Flashing JetPack, creating the user | Before any software can run | [Step 1](#3-step-1--flash-the-jetson-and-create-the-user) |
| Router admin password, firmware, SSH key | Before the script can reach the router | [Step 5](#7-step-5--prepare-the-router-by-hand-once) |
| GoodCloud unbind, saved repeater networks, tethering, auto-update | Admin-panel settings | [GL.iNet Setup §7](../glinet/initial.md#7-step-5--disable-cloud-repeater--dns-leaks) |
| WAN port label, live-cable WAN test, channel survey, RTC battery | Physical | [GL.iNet Setup §8–§9](../glinet/initial.md#8-step-6--verification-checklist) |
| Phones opening the student page on join | Needs real phones | [Captive Portal §7](../captive-portal.md#7-verification) |
| ESP32 clicker firmware | Separate toolchain | [`firmware/clicker`](../../firmware/clicker/README.md) |
| Audio output device and volume | Depends on the room's speakers | Desktop sound settings |

---

## <a id="15-status-and-troubleshooting"></a>15. Status and Troubleshooting

**Tested so far (2026-10-12, on the reference Jetson and router):** `jetson.yml --check --diff`,
`router.yml --check` and `verify.yml` end to end, and `router.sh apply` against a copy of the
router's configuration. **Not yet run on hardware:** `jetson.yml` and `router.yml` in apply mode,
the GPU build of the Qwen3-TTS daemon, and the classroom-screen unit in a desktop session. Expect to
adjust details the first time each one runs, and update this section when they have.

| Symptom | Cause | What to do |
| :--- | :--- | :--- |
| `No kit.yml in …` | The kit is not described yet | [Step 3](#5-step-3--describe-the-kit-kityml) |
| `sudo: a password is required` | `-K` is missing | Add `-K` |
| `uv … is expected` | A different `uv` is installed | `uv self update 0.12.13`, or run `./bootstrap.sh` |
| `--check` on a blank Jetson skips or fails late tasks | A check run installs nothing, so later tasks find no `node`, no units | Expected. Apply, then use `--check` for later changes |
| A run seems stuck on one task | Ansible prints nothing while a task runs | Follow the task's log from a second terminal ([Step 4](#6-step-4--set-up-the-jetson)) |
| The Ollama install, a model download or `run.py --prepare` fails | Ansible shows only the end of the task's log | Read the full log at the path Ansible prints, in `<repo>/.cache/logs/` |
| A package install fails or takes long (`packages`, `cuda`) | The playbook does not log `apt`; Ubuntu does | `tail -f /var/log/apt/term.log` |
| A log in `.cache/logs/` is old or missing | The task was skipped: nothing needed doing | Expected. A task writes its log only when it runs |
| `--require-cuda: no CUDA toolkit found` | The `cuda` part did not run or failed | `ansible-playbook jetson.yml -K --tags cuda`, then check `/usr/local/cuda/bin/nvcc` |
| `router.yml` fails with `Permission denied (publickey)` | The Jetson's key is not on the router | [Step 5](#7-step-5--prepare-the-router-by-hand-once), item 4 |
| `router.yml` reports `key: differs (value hidden)` forever | `wifi_passphrase` in `kit.yml` is still the placeholder | Set it. The passphrase is never printed |
| The screen stays on the desktop after reboot | The backend is not answering, so the unit is still waiting | `systemctl --user status utztutor-kiosk`, `systemctl status utztutor-backend` |
| No sound from the classroom screen | Wrong output device, or the policies file is missing | Desktop sound settings; `about:policies` in Firefox |

---

## Next Steps

* **[GL.iNet Initial Setup](../glinet/initial.md)**: Why each router setting exists, and the manual procedure the script follows.
* **[Captive Portal](../captive-portal.md)**: How the student page opens by itself on join, and how to verify it with real phones.
* **[Infrastructure Hub](../README.md)**: The services of the appliance and where each file lives.
* **[Hardware Topology](../../docs/architecture/hardware-topology.md)**: Offline appliance architecture and RAM budget.
