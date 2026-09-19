"""Custom colored and timestamped formatters for TutorBox application and server logs."""

from uvicorn.logging import AccessFormatter, ColourizedFormatter

DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
APP_LOG_FORMAT = "%(asctime)s %(levelprefix)s [%(name)s] %(message)s"
SERVER_LOG_FORMAT = "%(asctime)s %(levelprefix)s %(message)s"
ACCESS_LOG_FORMAT = '%(asctime)s %(levelprefix)s %(client_addr)-21s - "%(request_line)s" %(status_code)s'


class TutorBoxFormatter(ColourizedFormatter):
    """Application and server log formatter with ISO timestamps and colored level prefix."""

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = DEFAULT_DATE_FORMAT,
        use_colors: bool | None = None,
    ) -> None:
        super().__init__(
            fmt=fmt or APP_LOG_FORMAT,
            datefmt=datefmt,
            use_colors=use_colors,
        )


class TutorBoxAccessFormatter(AccessFormatter):
    """HTTP access log formatter with ISO timestamps, colored status codes, and request details."""

    def __init__(
        self,
        fmt: str | None = None,
        datefmt: str | None = DEFAULT_DATE_FORMAT,
        use_colors: bool | None = None,
    ) -> None:
        super().__init__(
            fmt=fmt or ACCESS_LOG_FORMAT,
            datefmt=datefmt,
            use_colors=use_colors,
        )
