"""Warning and critical limits of the Jetson health panel, in the units of each reading.

The limits judge this appliance: an 8 GB Jetson Orin Nano whose CPU and GPU share one
RAM pool, and which runs the quiz model and the offline voice next to each other.
Change them here and nowhere else; docs/api/system.md lists them for the teacher.
"""

# Temperature in degrees Celsius, the hottest zone counts. The Orin Nano throttles its
# clocks near 99 °C and shuts down near 104 °C: 80 °C is the point to check the fan and
# the enclosure, and 95 °C is close enough to throttling to act at once.
TEMPERATURE_WARN_CELSIUS = 80.0
TEMPERATURE_CRITICAL_CELSIUS = 95.0

# Memory the models and the voice can still use, in MB (1 GB = 1024 MB). The quiz model
# needs about 2.4 GB to sit entirely on the GPU; below 0.75 GB the next load cannot fit it.
MEMORY_AVAILABLE_WARN_MB = 1536.0
MEMORY_AVAILABLE_CRITICAL_MB = 768.0

# CPU usage over the last sample, all six cores together. Sustained use near this value
# leaves too little CPU for the voice and the web server.
CPU_USAGE_WARN_PERCENT = 85.0

# Free space on the partition that holds the database, in percent of its size. The
# database and the logs grow with every class, so a partition near full stops writes.
DISK_FREE_WARN_PERCENT = 10.0
DISK_FREE_CRITICAL_PERCENT = 5.0

# GPU load has no limit on purpose: it sits high during every question generation, which
# is the normal use of this board. The panel shows it for information only.
