import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from api.captive import captive_not_found_handler, foreign_host_redirect
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
# Keep RESERVED_PREFIXES in api/captive.py in sync when adding a mount.
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
    logger.info(
        "TutorBox Ready: Maestro -> http://localhost:8000/maestro/ | "
        "Alumno -> http://localhost:8000/alumno/ | "
        "Pantalla -> http://localhost:8000/pantalla/ | "
        "Docs -> http://localhost:8000/docs"
    )
    yield
    logger.info("Shutting down TutorBox backend appliance...")


app = FastAPI(
    title="TutorBox API",
    description="Offline Edge AI Socratic Educational Platform Backend",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(root_router)
# Captive portal: unknown pages requested through a hijacked name land on /alumno/.
app.add_exception_handler(404, captive_not_found_handler)
for _name in PILAS_MOUNTS:
    app.mount(
        f"/{_name}", StaticFiles(directory=PILAS_DIR / _name, html=True), name=_name
    )


@app.get("/", include_in_schema=False)
def pilas_root(request: Request) -> RedirectResponse:
    """Students land on the appliance address; the teacher opens /maestro/ explicitly.

    A hijacked name (a student typing any website, NetworkManager's root probe) is sent
    to the canonical address so the browser keeps one origin for its stored login.
    """
    return foreign_host_redirect(request) or RedirectResponse("/alumno/")
