from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.base import init_db

app = FastAPI(
    title="ExecAI",
    version="1.0.0",
)


@app.on_event("startup")
async def startup():
    init_db()


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


from app.routers.whatsapp import router as whatsapp_router

app.include_router(
    whatsapp_router,
    prefix="/webhook",
    tags=["WhatsApp"],
)