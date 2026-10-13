# Utz'tutor Infrastructure & Deployment

Deployment configurations, systemd service units, and isolated networking setup for the offline edge appliance.

<div align="center">

| 🏠 [Utz'tutor](../README.md) | 📚 [Docs](../docs/README.md) | ⚙️ [Backend](../backend/README.md) | 📱 [PWA](../pwa/README.md) | 🔌 **Infra** |
| :---: | :---: | :---: | :---: | :---: |

📍 **Infrastructure Hub** • **Related:** [Hardware Topology](../docs/architecture/hardware-topology.md) • [Backend Guide](../backend/README.md) • [Automated Kit Setup](ansible/README.md) • [GL.iNet Setup](glinet/initial.md) • [Captive Portal](captive-portal.md)

</div>

---

## 1. Subsystems & Services

* **Core AI Appliance (NVIDIA Jetson Orin Nano)**:
  * **Automated setup**: [`ansible/`](ansible/README.md) installs everything below on a blank Jetson and configures the router, the same way on every kit, and checks the result. Start there to build a kit.
  * **Systemd Service Units**: [`systemd/utztutor-backend.service.j2`](systemd/utztutor-backend.service.j2) supervises the FastAPI backend (`:8000`, serves the API and the Pilas pages). `ollama.service`, written by the Ollama installer, serves the quiz and tutor models on `127.0.0.1:11434`; the backend unit starts after it.
  * **Classroom screen (kiosk)**: [`kiosk/utztutor-kiosk.service`](kiosk/utztutor-kiosk.service) is a systemd user unit that opens `/pantalla/` full-screen in Firefox once the backend answers `/health`, and starts Firefox again if it closes. The Jetson has a screen but no keyboard, so the setup also turns on automatic login, stops the desktop from blanking or locking ([`kiosk/dconf-utztutor-kiosk`](kiosk/dconf-utztutor-kiosk)) and lets pages play sound without a click ([`kiosk/firefox-policies.json`](kiosk/firefox-policies.json)). The teacher then drives everything from `/maestro/` on a phone, including the class mode (quiz, tutor, take-home) — see [Three Modes §4](../docs/architecture/three-modes.md#4-choosing-the-mode).
  * **BLE Clicker Provisioner** (`utztutor-provisioner.service`, planned for Week 7): always-on Bluetooth GATT service that hands ESP32 clickers the classroom Wi-Fi and their device secret — see [ESP32 Clicker Protocol](../docs/architecture/esp32-protocol.md).
  * **Web Server & Reverse Proxy**: [`nginx/utztutor.conf`](nginx/utztutor.conf) publishes the backend on port 80 (`http://utztutor`, `http://192.168.8.2`) — required because phone captive-portal probes only use port 80. It also limits requests per address on three paths: login, signup and game event batches (the reasons are in the file).
  * **Captive Portal**: [`captive-portal.md`](captive-portal.md) — a phone that joins the Wi-Fi opens the student page automatically (router catch-all DNS + backend probe answers).
  * **Audio Output & TTS**: ALSA/PulseAudio configuration routing offline Spanish TTS and K'iche' native audio output to classroom speakers.
  * **System Tuning**: 25W clock caps applied at boot by [`systemd/utztutor-power.service.j2`](systemd/utztutor-power.service.j2), because nvpmodel's own boot step fails on this board (the unit header explains why). The desktop stays on for now, and `jetson_clocks` is not used: it pins clocks at maximum, which raises sustained current.
* **Isolated Classroom AP (GL.iNet GL-AR300M16)**:
  * Local DHCP configuration broadcasting SSID `Utz'tutor`.
  * dnsmasq static lease `utztutor` → `192.168.8.2` and catch-all DNS (every name resolves to the Jetson).
  * WAN port disabled to guarantee 100% offline security.
  * [`glinet/router.sh`](glinet/router.sh) applies these settings, or lists how a router differs from them.

---

## Next Steps

* **[Automated Kit Setup](ansible/README.md)**: Build a kit step by step with the Ansible playbooks.
* **[GL.iNet Initial Setup](glinet/initial.md)**: Why each router setting exists (Wi-Fi, DHCP, DNS, WAN kill), and the manual procedure.
* **[Captive Portal](captive-portal.md)**: How the student page opens by itself on join, and how to verify it.
* **[Hardware Topology](../docs/architecture/hardware-topology.md)**: Review detailed offline appliance architecture and RAM memory budget.
* **[Backend Developer Guide](../backend/README.md)**: Setup the FastAPI server and local development environment.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
