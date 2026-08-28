# TutorBox Infrastructure & Deployment

Deployment configurations, systemd service units, and isolated networking setup for the offline edge appliance.

> [TutorBox](../README.md) / **Infrastructure** • [Documentation](../docs/README.md) • [Backend](../backend/README.md) • [Hardware Topology](../docs/architecture/hardware-topology.md)

---

## 1. Subsystems & Services

* **Core AI Appliance (NVIDIA Jetson Orin Nano)**:
  * **Systemd Service Units**: Process supervision for `llama.cpp` inference server, FastAPI backend (`:8000`), and HDMI classroom display.
  * **Web Server & Reverse Proxy**: Nginx configuration serving compiled PWA static files and routing API/WebSocket connections.
  * **Audio Output & TTS**: ALSA/PulseAudio configuration routing offline Spanish TTS and K'iche' native audio output to classroom speakers.
  * **System Tuning**: Headless mode, 25W performance mode, and persistent `jetson_clocks` execution.
* **Isolated Classroom AP (GL.iNet GL-AR300M16)**:
  * Local DHCP configuration broadcasting SSID `TutorBox`.
  * WAN port disabled to guarantee 100% offline security.

---

## Next Steps

* **[Hardware Topology](../docs/architecture/hardware-topology.md)**: Review detailed offline appliance architecture and RAM memory budget.
* **[Backend Developer Guide](../backend/README.md)**: Setup the FastAPI server and local development environment.
* **[Documentation Portal](../docs/README.md)**: View the overarching documentation index.
