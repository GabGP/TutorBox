"""Console output tags and shared messages for the Utz'tutor launcher.

Single source of truth for user-facing runner output; backend tests assert on
the message bodies.
"""

TAG_INFO = "[\033[33mINFO\033[0m]"
TAG_WARN = "[\033[33mWARN\033[0m]"
TAG_FAIL = "[\033[31mFAIL\033[0m]"
TAG_BUILD = "[\033[34mBUILD\033[0m]"
TAG_OK = "[\033[32mOK\033[0m]"

BANNER_LINE = "=================================================="
SEPARATOR_LINE = "--------------------------------------------------"

PWA_DIST_LABEL = ".cache/pwa/dist"
PWA_BUILD_CMD = "pnpm --dir pwa/app run build"
LEGACY_CLIENT_ENV = "PWA_STATIC_DIR=pwa/pilas"
MSG_BACKEND_FAIL_FAST = f"Backend default ({PWA_DIST_LABEL}) will fail fast on startup."


def print_banner() -> None:
    """Prints the appliance startup banner."""
    print(BANNER_LINE)
    print("      Starting Utz'tutor Edge AI Appliance         ")
    print(BANNER_LINE)


def print_separator() -> None:
    """Prints the divider shown between launcher steps."""
    print(SEPARATOR_LINE)


def print_fail_fast_hint() -> None:
    """Shared closing note when the PWA bundle is unavailable."""
    print(f"       {MSG_BACKEND_FAIL_FAST}")
    print(f"       Explicitly set {LEGACY_CLIENT_ENV} for the legacy client.")
