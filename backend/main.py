import os
import sys
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from routes.process import router as process_router
from routes.drill import router as drill_router

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


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    print(f">> {request.method} {request.url.path} (started)", flush=True)
    response = await call_next(request)
    elapsed = time.perf_counter() - start
    print(f"<< {request.method} {request.url.path} -> {response.status_code} in {elapsed:.1f}s", flush=True)
    return response


app.include_router(process_router, prefix="/api")
app.include_router(drill_router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
