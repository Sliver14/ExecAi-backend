from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import time
import logging
from pythonjsonlogger import jsonlogger
from app.db.base import init_db
from app.core.config import get_settings

# Configure structured logging
logger = logging.getLogger("execai.main")
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s')
logHandler.setFormatter(formatter)
logging.basicConfig(level=logging.INFO, handlers=[logHandler])

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Starting up ExecAI service...")
    try:
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {e}", exc_info=True)
    yield
    # Shutdown sequence
    logger.info("Shutting down ExecAI service...")

app = FastAPI(
    title="ExecAI",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False,
)

# Global custom logging & timing middleware
@app.middleware("http")
async def log_requests_and_timing(request: Request, call_next):
    start_time = time.time()
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        logger.info(
            f"Request completed: {request.method} {request.url.path} - "
            f"Status: {response.status_code} - Duration: {process_time:.4f}s"
        )
        return response
    except Exception as exc:
        process_time = time.time() - start_time
        logger.error(
            f"Unhandled exception during: {request.method} {request.url.path} - "
            f"Error: {exc} - Duration: {process_time:.4f}s",
            exc_info=True
        )
        return Response(
            content='{"detail": "Internal Server Error"}',
            status_code=500,
            media_type="application/json"
        )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "ExecAI API running"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy"
    }

@app.get("/ready")
async def ready():
    # Basic readiness check verifying database connectivity
    from app.db.base import engine
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Readiness check failed database connection: {e}")
        return Response(
            content='{"status": "unready", "database": "disconnected"}',
            status_code=503,
            media_type="application/json"
        )

from app.routers.whatsapp import router as whatsapp_router
from app.routers.oauth import router as oauth_router

app.include_router(
    whatsapp_router,
    prefix="/webhook",
    tags=["WhatsApp"],
)

app.include_router(
    oauth_router,
    prefix="/oauth/google",
    tags=["Google OAuth"],
)