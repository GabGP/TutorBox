import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.auth import router as auth_router
from api.health import router as health_router
from db.database import get_db_path
from db.migrations import apply_migrations

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("tutorbox")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TutorBox backend appliance...")
    db_path = get_db_path()
    logger.info(f"Running database migrations on {db_path}...")
    apply_migrations(db_path)
    logger.info("Database migrations complete.")
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
