#!/bin/sh
# Utz'tutor — configure the GL.iNet classroom router, or report how it differs.
#
# The same settings as the manual runbook (infra/glinet/initial.md §4–§7), each written once:
#   router.sh verify   prints every difference and changes nothing
#   router.sh apply    makes the changes, commits them and reloads what changed
# Both are safe to repeat. apply on a router that already matches changes nothing.
#
# Runs ON the router (OpenWrt, busybox sh, no Python). infra/ansible/router.yml sends it over
# SSH with the kit's values; by hand:
#   { cat kit.env; cat infra/glinet/router.sh; } | ssh root@192.168.8.1 sh -s verify
# where kit.env holds the variables below, one VAR='value' per line.
#
# Required: WIFI_SSID WIFI_KEY WIFI_CHANNEL WIFI_COUNTRY WIFI_HTMODE JETSON_IP JETSON_MAC
#           DNS_NAME DHCP_START DHCP_LIMIT DHCP_LEASETIME
# Optional: DISABLE_SERVICES (init scripts to stop and disable, space separated),
#           AP_IFACE (wifi-iface section of the classroom AP; found by itself when empty),
#           FIRMWARE (GL.iNet firmware version the router must run, as in /etc/glversion;
#           checked, never installed: verify reports a difference, apply only notes it)
#
# Not covered, still done by hand in the admin panel (initial.md §3 and §7): firmware update,
# admin password, SSH key, GoodCloud unbind, saved repeater networks, tethering, auto-update.
#
# The last line printed is "RESULT drift=N" (verify) or "RESULT changed=N" (apply).

set -u

MODE=${1:-}
case "$MODE" in
    verify | apply) ;;
    *) echo "usage: router.sh verify|apply" >&2; exit 2 ;;
esac

for name in WIFI_SSID WIFI_KEY WIFI_CHANNEL WIFI_COUNTRY WIFI_HTMODE JETSON_IP JETSON_MAC \
    DNS_NAME DHCP_START DHCP_LIMIT DHCP_LEASETIME; do
    eval "value=\${$name:-}"
    [ -n "$value" ] || { echo "router.sh: $name is not set" >&2; exit 2; }
done

DISABLE_SERVICES=${DISABLE_SERVICES:-}
AP_IFACE=${AP_IFACE:-}
FIRMWARE=${FIRMWARE:-}
# Overridable so the script can be tested off the router.
RC_LOCAL=${RC_LOCAL:-/etc/rc.local}
INIT_DIR=${INIT_DIR:-/etc/init.d}
GLVERSION_FILE=${GLVERSION_FILE:-/etc/glversion}

JETSON_MAC=$(echo "$JETSON_MAC" | tr 'A-F' 'a-f')

count=0         # differences found (verify) or changes made (apply)
touched=""      # uci packages with pending changes

# Reports one difference; returns 0 when the caller should now make the change.
differs() {
    count=$((count + 1))
    if [ "$MODE" = apply ]; then
        echo "change  $1"
        return 0
    fi
    echo "DRIFT   $1"
    return 1
}

touch_package() {
    case " $touched " in
        *" $1 "*) ;;
        *) touched="$touched $1" ;;
    esac
}

# want <package.section.option> <value> [secret]: the option must hold exactly this value.
want() {
    current=$(uci -q get "$1")
    [ "$current" = "$2" ] && return 0
    if [ -n "${3:-}" ]; then
        message="$1: differs (value hidden)"
    else
        message="$1: is '$current', want '$2'"
    fi
    if differs "$message"; then
        uci set "$1=$2"
        touch_package "${1%%.*}"
    fi
}

# absent <package.section[.option]>: the option or section must not exist.
absent() {
    uci -q get "$1" >/dev/null || return 0
    if differs "$1: present, want it removed"; then
        uci delete "$1"
        touch_package "${1%%.*}"
    fi
}

# want_list <package.section.option> <value>...: the list must hold exactly these values.
want_list() {
    key=$1
    shift
    current=$(uci -q get "$key")
    for item in $current; do
        keep=0
        for wanted in "$@"; do
            [ "$item" = "$wanted" ] && keep=1
        done
        [ $keep = 1 ] && continue
        if differs "$key: has '$item', want it removed"; then
            uci del_list "$key=$item"
            touch_package "${key%%.*}"
        fi
    done
    for wanted in "$@"; do
        case " $current " in
            *" $wanted "*) continue ;;
        esac
        if differs "$key: lacks '$wanted'"; then
            uci add_list "$key=$wanted"
            touch_package "${key%%.*}"
        fi
    done
}

# Section names of one type in a package, one per line: named sections by name,
# anonymous ones as @type[index].
sections() {
    uci -q show "$1" | sed -n "s/^$1\.\([^.=]*\)=$2\$/\1/p"
}

# remove_sections <package> <type> <option> <value>: deletes every section of that type
# whose option has that value. Highest index first, so the other indexes stay valid.
remove_sections() {
    for section in $(sections "$1" "$2" | sed '1!G;h;$!d'); do
        [ "$(uci -q get "$1.$section.$3")" = "$4" ] || continue
        if differs "$1.$section ($3='$4'): present, want it removed"; then
            uci delete "$1.$section"
            touch_package "$1"
        fi
    done
}

# ---- §3 Firmware ---------------------------------------------------------------------------

# A script cannot flash the router, so apply only notes the difference and the check that
# follows apply reports it.
if [ -n "$FIRMWARE" ]; then
    firmware_found=$(cat "$GLVERSION_FILE" 2>/dev/null)
    if [ "$firmware_found" != "$FIRMWARE" ]; then
        firmware_message="firmware: is '${firmware_found:-unknown}', want '$FIRMWARE'"
        if [ "$MODE" = apply ]; then
            echo "note    $firmware_message; flash it in the admin panel (initial.md §3)"
        else
            differs "$firmware_message"
        fi
    fi
fi

# ---- §4 Wi-Fi ----------------------------------------------------------------------------

if [ -z "$AP_IFACE" ]; then
    for section in $(sections wireless wifi-iface); do
        [ "$(uci -q get "wireless.$section.mode")" = ap ] || continue
        [ "$(uci -q get "wireless.$section.network")" = lan ] || continue
        AP_IFACE=$section
        break
    done
fi
[ -n "$AP_IFACE" ] || { echo "router.sh: no access-point interface on the lan network" >&2; exit 2; }
RADIO=$(uci -q get "wireless.$AP_IFACE.device")
[ -n "$RADIO" ] || { echo "router.sh: wireless.$AP_IFACE has no device" >&2; exit 2; }

want "wireless.$RADIO.disabled" 0
want "wireless.$RADIO.channel" "$WIFI_CHANNEL"
want "wireless.$RADIO.htmode" "$WIFI_HTMODE"
want "wireless.$RADIO.country" "$WIFI_COUNTRY"
want "wireless.$AP_IFACE.mode" ap
want "wireless.$AP_IFACE.ssid" "$WIFI_SSID"
want "wireless.$AP_IFACE.encryption" psk2+ccmp
want "wireless.$AP_IFACE.key" "$WIFI_KEY" secret
want "wireless.$AP_IFACE.hidden" 0
want "wireless.$AP_IFACE.isolate" 1

# §7.2: a station-mode interface is a wireless uplink. None may be enabled.
for section in $(sections wireless wifi-iface); do
    [ "$(uci -q get "wireless.$section.mode")" = sta ] || continue
    want "wireless.$section.disabled" 1
done

# ---- §5 LAN, DHCP, static lease, catch-all DNS ---------------------------------------------

want dhcp.lan.start "$DHCP_START"
want dhcp.lan.limit "$DHCP_LIMIT"
want dhcp.lan.leasetime "$DHCP_LEASETIME"

# One lease for the Jetson, in the section dhcp.jetson. Any other lease that claims the same
# name, address or MAC would compete with it.
for section in $(sections dhcp host | sed '1!G;h;$!d'); do
    [ "$section" = jetson ] && continue
    lease_mac=$(uci -q get "dhcp.$section.mac" | tr 'A-F' 'a-f')
    if [ "$(uci -q get "dhcp.$section.name")" = "$DNS_NAME" ] ||
        [ "$(uci -q get "dhcp.$section.ip")" = "$JETSON_IP" ] ||
        [ "$lease_mac" = "$JETSON_MAC" ]; then
        if differs "dhcp.$section: another lease for the Jetson, want it removed"; then
            uci delete "dhcp.$section"
            touch_package dhcp
        fi
    fi
done
lease=present
if ! uci -q get dhcp.jetson >/dev/null; then
    lease=missing
    if differs "dhcp.jetson: no lease '$DNS_NAME' -> $JETSON_IP for $JETSON_MAC"; then
        uci set dhcp.jetson=host
        touch_package dhcp
        lease=present
    fi
fi
if [ $lease = present ]; then
    want dhcp.jetson.name "$DNS_NAME"
    want dhcp.jetson.mac "$JETSON_MAC"
    want dhcp.jetson.ip "$JETSON_IP"
    want dhcp.jetson.dns 1      # publish the name even before the lease is active
fi

# '/./' is the form dnsmasq 2.86 (GL.iNet 4.3.x) honours; '/#/' is for newer builds (§5b).
want_list "dhcp.@dnsmasq[0].address" "/./$JETSON_IP" "/#/$JETSON_IP"

# ---- §6 Kill the WAN path, four layers ---------------------------------------------------

# Read before layer 1, which keeps the section but disables it.
WAN_DEVICE=$(uci -q get network.wan.device || uci -q get network.wan.ifname)

# Layer 1: the WAN interfaces.
if uci -q get network.wan >/dev/null; then
    want network.wan.disabled 1
    want network.wan.auto 0
fi
absent network.wan6

# Layer 2: every forwarding into the wan zone, then the zone.
remove_sections firewall forwarding dest wan
remove_sections firewall zone name wan

# Layer 3: no default route source.
absent network.lan.gateway

# Layer 4: hold the physical port down at boot.
if [ -n "$WAN_DEVICE" ]; then
    port_down="ip link set $WAN_DEVICE down"
    if ! grep -qxF "$port_down" "$RC_LOCAL" 2>/dev/null; then
        if differs "$RC_LOCAL: lacks '$port_down'"; then
            # Above the trailing 'exit 0', or at the end when there is none.
            awk -v line="$port_down" '
                !placed && /^exit 0/ { print line; placed = 1 }
                { print }
                END { if (!placed) print line }
            ' "$RC_LOCAL" >"$RC_LOCAL.new" && cat "$RC_LOCAL.new" >"$RC_LOCAL"
            rm -f "$RC_LOCAL.new"
            $port_down
        fi
    fi
else
    echo "note    network.wan has no device: layer 4 (port held down in $RC_LOCAL) skipped"
fi

# ---- §7 Cloud services and DNS leaks -----------------------------------------------------

for service in $DISABLE_SERVICES; do
    [ -x "$INIT_DIR/$service" ] || continue
    "$INIT_DIR/$service" enabled || continue
    if differs "service $service: enabled, want it stopped and disabled"; then
        "$INIT_DIR/$service" stop >/dev/null 2>&1
        "$INIT_DIR/$service" disable
    fi
done

want "dhcp.@dnsmasq[0].noresolv" 1
absent "dhcp.@dnsmasq[0].resolvfile"
absent "dhcp.@dnsmasq[0].server"

# ---- Commit and reload (apply only) --------------------------------------------------------

if [ "$MODE" = apply ]; then
    for package in $touched; do
        uci commit "$package"
    done
    case " $touched " in *" dhcp "*)
        echo "reload  dnsmasq"
        "$INIT_DIR/dnsmasq" restart
        ;;
    esac
    case " $touched " in *" firewall "*)
        echo "reload  firewall"
        "$INIT_DIR/firewall" restart >/dev/null 2>&1
        ;;
    esac
    # A network restart also restarts the radio. Either one disconnects Wi-Fi clients for a
    # few seconds; the wired Jetson keeps its link.
    case " $touched " in
        *" network "*)
            echo "reload  network (Wi-Fi clients reconnect)"
            "$INIT_DIR/network" restart
            ;;
        *" wireless "*)
            echo "reload  wifi (Wi-Fi clients reconnect)"
            wifi reload
            ;;
    esac
    echo "RESULT changed=$count"
    exit 0
fi

# Not a setting: what the routing table says right now.
if [ -n "$(ip route show default 2>/dev/null)" ]; then
    count=$((count + 1))
    echo "DRIFT   routing table: has a default route, want none"
fi
echo "RESULT drift=$count"
