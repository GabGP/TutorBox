"""Default configuration constants for TutorBox edge appliance."""

from pathlib import Path

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent.parent.parent

DEFAULT_DB_PATH: str = str(PROJECT_ROOT / ".cache" / "db" / "tutorbox.db")
DEFAULT_BUSY_TIMEOUT_MS: int = 5000

DEFAULT_BCRYPT_ROUNDS: int = 12
DEFAULT_AUTH_MAX_ATTEMPTS: int = 5
DEFAULT_AUTH_LOCKOUT_SECONDS: int = 30
DEFAULT_AUTH_MAX_TRACKED_KEYS: int = 10_000
DEFAULT_SIGNUP_MAX_EVENTS: int = 30
DEFAULT_SIGNUP_WINDOW_SECONDS: int = 60
# Bootstrap teacher created at startup; set SEED_TEACHER_PIN= (empty) to disable.
DEFAULT_SEED_TEACHER_USERNAME: str = "teacher1"
DEFAULT_SEED_TEACHER_PIN: str = "1234"

DEFAULT_SLM_BASE_URL: str = "http://127.0.0.1:8080/v1"
DEFAULT_SLM_MODEL_NAME: str = "default"
DEFAULT_SLM_TEMPERATURE: float = 0.7
DEFAULT_SLM_TIMEOUT_SECONDS: float = 60.0

DEFAULT_QUIZ_MAX_RETRIES: int = 3

# Offline classroom voice (espeak-ng) used by the >51% spoken intervention.
DEFAULT_TTS_ENABLED: bool = True
DEFAULT_TTS_BINARY: str = ""  # empty: auto-detect espeak-ng, then legacy espeak
DEFAULT_TTS_VOICE: str = "es-419"  # espeak-ng Latin American Spanish
DEFAULT_TTS_VOICE_QUC: str = ""  # no K'iche' voice ships with espeak-ng yet
DEFAULT_TTS_WORDS_PER_MINUTE: int = (
    150  # slower than the 175 default, for primary school
)
DEFAULT_TTS_PITCH: int = 45
DEFAULT_TTS_AMPLITUDE: int = 180
DEFAULT_TTS_TIMEOUT_SECONDS: float = 10.0
DEFAULT_TTS_MAX_CHARS: int = 600

# Captive portal: answer phone connectivity probes with a redirect to the student
# page so the OS sign-in browser opens it automatically when a device joins the AP.
DEFAULT_CAPTIVE_PORTAL_ENABLED: bool = True
DEFAULT_CAPTIVE_PORTAL_URL: str = "http://tutorbox/alumno/"
