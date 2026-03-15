import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import forecast, summary
from app.core.config import settings

app = FastAPI(
    title="HARIBON: Harmful Algal Bloom Intelligent Observer Network",
    version="2.0.0",
    description="AI-powered early warning system for proactive red tide risk forecasting in Western Visayas, Philippines"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(forecast.router, prefix="/api/forecast")
app.include_router(summary.router, prefix="/api/summary")

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} v2.0!",
        "description": "Enhanced red tide prediction system with comprehensive environmental features",
        "docs": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    # Pass import string to enable reload
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)