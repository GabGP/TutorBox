"""Host RAM, GPU VRAM and Jetson UMA memory monitoring for TTS benchmark runs."""

from __future__ import annotations

from tools.benchmark.tts.memory.host_rss import get_host_rss_mb
from tools.benchmark.tts.memory.jetson import is_jetson_uma
from tools.benchmark.tts.memory.monitor import MemoryMonitor
from tools.benchmark.tts.memory.nvml import NVMLTracker

__all__ = [
    "MemoryMonitor",
    "NVMLTracker",
    "get_host_rss_mb",
    "is_jetson_uma",
]
