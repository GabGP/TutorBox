"""Logging filters for TutorBox server and access logs."""

import logging

PROBE_PATHS: frozenset[str] = frozenset(
    {
        "/generate_204",
        "/gen_204",
        "/hotspot-detect.html",
        "/library/test/success.html",
        "/connecttest.txt",
        "/ncsi.txt",
        "/redirect",
        "/success.txt",
        "/canonical.html",
        "/check_network_status.txt",
    }
)


class ProbeFilter(logging.Filter):
    """Filters out noisy captive portal probes from Uvicorn access logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Returns False if log record matches known captive portal probes."""
        if not record.args or len(record.args) < 3:
            return True
        path = str(record.args[2])
        return path not in PROBE_PATHS
