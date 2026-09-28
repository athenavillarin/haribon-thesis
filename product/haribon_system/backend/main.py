import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from app.api import forecast, summary
from app.core.config import settings

app = FastAPI(
    title="HARIBON: Harmful Algal Bloom Intelligent Observer Network",
    version="2.0.0",
    description="AI-powered early warning system for proactive red tide risk forecasting in Western Visayas, Philippines"
)

# Parse allowed origins: if "*", allow all; otherwise split comma-separated list
if settings.ALLOWED_ORIGINS == "*":
    cors_origins = ["*"]
else:
    cors_origins = [origin.strip() for origin in settings.ALLOWED_ORIGINS.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_cache_headers(request: Request, call_next):
    response = await call_next(request)
    if request.method == "GET" and request.url.path.startswith("/api/") and response.status_code == 200:
        response.headers.setdefault("Cache-Control", "public, max-age=600")
    return response


app.include_router(forecast.router, prefix="/api/forecast")
app.include_router(summary.router, prefix="/api/summary")

@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} v2.0!",
        "description": "Enhanced red tide prediction system with comprehensive environmental features",
        "docs": "/docs"
    }

@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"status": "alive"}

if __name__ == "__main__":
    import uvicorn
    # Pass import string to enable reload
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
