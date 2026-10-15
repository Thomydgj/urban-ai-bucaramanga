
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Raíz del proyecto:
# urban-ai-bucaramanga/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Cargar explícitamente el archivo .env de la raíz.
load_dotenv(PROJECT_ROOT / ".env")

from .routers import (
    health,
    segmentation,
    summary,
    zones,
    intervention_planner,
)

app = FastAPI(
    title="Urban AI Bucaramanga API",
    description=(
        "API para consulta de zonas prioritarias "
        "de intervención urbana."
    ),
    version="1.0.0",
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "https://urban-ai-bucaramanga.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# ROOT
# =========================================================

@app.get("/")
def root():

    return {
        "name": "Urban AI Bucaramanga API",
        "version": "1.0.0",
        "status": "running",
    }


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    health.router
)

app.include_router(
    summary.router
)

app.include_router(
    zones.router
)

app.include_router(
    segmentation.router
)

app.include_router(
    intervention_planner.router
)