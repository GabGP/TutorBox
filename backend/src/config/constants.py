"""Default configuration constants for TutorBox edge appliance."""

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent

DEFAULT_DB_PATH: str = str(PROJECT_ROOT / ".cache" / "db" / "tutorbox.db")
DEFAULT_BUSY_TIMEOUT_MS: int = 5000

DEFAULT_BCRYPT_ROUNDS: int = 12
DEFAULT_AUTH_MAX_ATTEMPTS: int = 5
DEFAULT_AUTH_LOCKOUT_SECONDS: int = 30
DEFAULT_AUTH_MAX_TRACKED_KEYS: int = 10_000
DEFAULT_SIGNUP_MAX_EVENTS: int = 30
DEFAULT_SIGNUP_WINDOW_SECONDS: int = 60

DEFAULT_SLM_BASE_URL: str = "http://127.0.0.1:8080/v1"
DEFAULT_SLM_MODEL_NAME: str = "default"
DEFAULT_SLM_TEMPERATURE: float = 0.7
DEFAULT_SLM_TIMEOUT_SECONDS: float = 60.0

DEFAULT_QUIZ_MAX_RETRIES: int = 3
