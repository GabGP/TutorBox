import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.router import root_router
from core.config import load_env_file
from core.db.database import get_db_path
from core.db.migrations import apply_migrations
from core.db.seed_users import seed_teacher
from modes.quiz.seed_data import seed_question_bank

load_env_file()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tutorbox")
# Pilas classroom client (pwa/pilas) served same-origin so pages call /api/v1 directly.
# Mounted per folder (not at "/") so unknown API paths keep their JSON 404 and slash redirects.
PILAS_DIR = Path(__file__).resolve().parents[2] / "pwa" / "pilas"
PILAS_MOUNTS = ("maestro", "alumno", "pantalla", "static")


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
    if seed_teacher(db_path):
        logger.info("Bootstrap teacher account created.")
    yield
    logger.info("Shutting down TutorBox backend appliance...")


app = FastAPI(
    title="TutorBox API",
    description="Offline Edge AI Socratic Educational Platform Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(root_router)
for _name in PILAS_MOUNTS:
    app.mount(
        f"/{_name}", StaticFiles(directory=PILAS_DIR / _name, html=True), name=_name
    )


@app.get("/", include_in_schema=False)
def pilas_root() -> RedirectResponse:
    """Students land on the appliance address; the teacher opens /maestro/ explicitly."""
    return RedirectResponse("/alumno/")
