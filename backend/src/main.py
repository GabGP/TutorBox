import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import APIRouter, FastAPI

from api.auth import router as auth_router
from api.health import router as health_router
from api.quiz import router as quiz_router
from api.staff import router as staff_router
from api.users import router as users_router
from db.database import get_db_path
from db.migrations import apply_migrations
from quiz.seed_data import seed_question_bank


def load_env_file() -> None:
    """Loads environment variables from root or backend .env file if present."""
    search_paths = [
        Path(__file__).resolve().parent.parent.parent / ".env",
        Path(__file__).resolve().parent.parent / ".env",
    ]
    for env_path in search_paths:
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("#") or "=" not in stripped:
                    continue
                key, val = stripped.split("=", 1)
                clean_key, clean_val = key.strip(), val.strip().strip("'\"")
                if clean_key and clean_key not in os.environ:
                    os.environ[clean_key] = clean_val
            break


load_env_file()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tutorbox")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TutorBox backend appliance...")
    db_path = get_db_path()
    logger.info("Running database migrations on %s...", db_path)
    apply_migrations(db_path)
    logger.info("Database migrations complete.")
    logger.info("Verifying and seeding default quiz question bank...")
    seeded_count = seed_question_bank(db_path)
    logger.info("Question bank ready (newly seeded questions: %d).", seeded_count)
    yield
    logger.info("Shutting down TutorBox backend appliance...")


app = FastAPI(
    title="TutorBox API",
    description="Offline Edge AI Socratic Educational Platform Backend",
    version="0.1.0",
    lifespan=lifespan,
)

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router, prefix="/auth")
api_v1_router.include_router(users_router, prefix="/users")
api_v1_router.include_router(staff_router, prefix="/staff")
api_v1_router.include_router(quiz_router, prefix="/quiz")

app.include_router(health_router)
app.include_router(api_v1_router)
