# TutorBox Infrastructure & Deployment

Deployment configurations, systemd service units, and isolated networking setup for the offline edge appliance.

<div align="center">

| 🏠 [TutorBox](../README.md) | 📚 [Docs](../docs/README.md) | ⚙️ [Backend](../backend/README.md) | 📱 [PWA](../pwa/README.md) | 🔌 **Infra** |
| :---: | :---: | :---: | :---: | :---: |

📍 **Infrastructure Hub** • **Related:** [Hardware Topology](../docs/architecture/hardware-topology.md) • [Backend Guide](../backend/README.md) • [GL.iNet Setup](glinet/initial.md) • [Captive Portal](captive-portal.md)

</div>

---

## 1. Subsystems & Services

* **Core AI Appliance (NVIDIA Jetson Orin Nano)**:
  * **Systemd Service Units**: [`systemd/tutorbox-backend.service`](systemd/tutorbox-backend.service) supervises the FastAPI backend (`:8000`, serves the API and the Pilas pages); `llama.cpp` inference server and HDMI classroom display units are still to come.
  * **BLE Clicker Provisioner** (`tutorbox-provisioner.service`, planned for Week 7): always-on Bluetooth GATT service that hands ESP32 clickers the classroom Wi-Fi and their device secret — see [ESP32 Clicker Protocol](../docs/architecture/esp32-protocol.md).
  * **Web Server & Reverse Proxy**: [`nginx/tutorbox.conf`](nginx/tutorbox.conf) publishes the backend on port 80 (`http://tutorbox`, `http://192.168.8.2`) — required because phone captive-portal probes only use port 80.
  * **Captive Portal**: [`captive-portal.md`](captive-portal.md) — a phone that joins the Wi-Fi opens the student page automatically (router catch-all DNS + backend probe answers).
  * **Audio Output & TTS**: ALSA/PulseAudio configuration routing offline Spanish TTS and K'iche' native audio output to classroom speakers.
  * **System Tuning**: Headless mode, 25W performance mode, and persistent `jetson_clocks` execution.
* **Isolated Classroom AP (GL.iNet GL-AR300M16)**:
  * Local DHCP configuration broadcasting SSID `TutorBox`.
  * dnsmasq static lease `tutorbox` → `192.168.8.2` and catch-all DNS (every name resolves to the Jetson).
  * WAN port disabled to guarantee 100% offline security.

---

## Next Steps

* **[GL.iNet Initial Setup](glinet/initial.md)**: Provision the isolated classroom AP (Wi-Fi, DHCP, DNS, WAN kill).
* **[Captive Portal](captive-portal.md)**: How the student page opens by itself on join, and how to verify it.
* **[Hardware Topology](../docs/architecture/hardware-topology.md)**: Review detailed offline appliance architecture and RAM memory budget.
* **[Backend Developer Guide](../backend/README.md)**: Setup the FastAPI server and local development environment.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
