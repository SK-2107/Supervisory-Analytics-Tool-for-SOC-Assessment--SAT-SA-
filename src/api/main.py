"""
FastAPI Main Application Entrypoint for SAT-SA.
"""

import os
import sys
from pathlib import Path

# Ensure project root directory is in sys.path
_project_root = str(Path(__file__).resolve().parent.parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from src.db.connection import get_db_connection
from src.api.routes import ingest, analytics, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB on startup
    conn = get_db_connection()
    conn.close()
    yield


app = FastAPI(
    title="SAT-SA API",
    description="Supervisory Analytics Tool for SOC Assessment (SIH26157)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest.router)
app.include_router(analytics.router)
app.include_router(reports.router)


@app.get("/")
def root():
    return {
        "system": "Supervisory Analytics Tool for SOC Assessment (SAT-SA)",
        "problem_statement": "SIH26157",
        "status": "ONLINE (Air-gapped local execution)",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=8000, reload=True)
