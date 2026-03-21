import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.process import router as process_router

app = FastAPI(
    title="Headcount Dashboard API",
    description="FastAPI backend for the BCG Headcount Dashboard",
    version="1.0.0",
)

allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", "*")
allowed_origins = [o.strip() for o in allowed_origins_raw.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(process_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
