from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings
from app.db.base import engine, Base, init_db
import app.models  # Import all models to register them

app = FastAPI(title="ExecAI", version="1.0.0")

@app.on_event("startup")
def startup_event():
    init_db()


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "ExecAI WhatsApp Assistant is running!"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Routers
from app.routers.whatsapp import router as whatsapp_router
app.include_router(whatsapp_router, prefix="/webhook", tags=["whatsapp"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
