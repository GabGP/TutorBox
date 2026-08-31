import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.health import router as health_router
from api.quiz import router as quiz_router
from api.staff import router as staff_router
from api.users import router as users_router
from db.database import get_db_path
from db.migrations import apply_migrations
from quiz.seed_data import seed_question_bank

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

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(staff_router)
app.include_router(quiz_router)
