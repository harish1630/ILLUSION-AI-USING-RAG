"""Main FastAPI application entrypoint for ILLUSION AI."""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.db.supabase import init_db
from app.routes.health import router as health_router
from app.routes.languages import router as languages_router
from app.routes.schemes import router as schemes_router
from app.routes.business import router as business_router
from app.routes.roadmap import router as roadmap_router
from app.routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    init_db()
    yield
    logger.info(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered platform guiding first-time entrepreneurs through business startup and government schemes in Tamil Nadu & India.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root health route
app.include_router(health_router)

# API v1 routes
app.include_router(languages_router, prefix=settings.API_V1_PREFIX)
app.include_router(schemes_router, prefix=settings.API_V1_PREFIX)
app.include_router(business_router, prefix=settings.API_V1_PREFIX)
app.include_router(roadmap_router, prefix=settings.API_V1_PREFIX)
app.include_router(chat_router, prefix=settings.API_V1_PREFIX)


# Root health and info route
@app.get("/")
async def root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0",
        "api_v1": settings.API_V1_PREFIX,
    }


@app.get("/api")
async def api_info():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "version": "1.0.0",
        "api_v1": settings.API_V1_PREFIX,
    }

#multi  processing

import multiprocessing

def main():
    # Your application code here
    print("Application started")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()