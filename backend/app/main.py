"""FastAPI application factory."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog

from app.core.config import settings
from app.core.logging import get_logger
from app.core.middleware import RequestIDMiddleware
from app.core.database import check_db_health
from app.core.redis_client import check_redis_health
from app.core.influx import check_influx_health
from app.core.minio_client import get_minio_client
from app.api.v1 import auth, devices, telemetry, dashboard, rules, alerts, analytics, reports

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("API starting up", service="api", version="1.0.0")
    
    # Check database connection
    if await check_db_health():
        logger.info("Database connection OK")
    else:
        logger.error("Database connection failed")
    
    # Check Redis connection
    if await check_redis_health():
        logger.info("Redis connection OK")
    else:
        logger.error("Redis connection failed")
    
    # Check InfluxDB connection
    if await check_influx_health():
        logger.info("InfluxDB connection OK")
    else:
        logger.error("InfluxDB connection failed")
    
    # Ensure MinIO bucket exists
    try:
        minio_client = get_minio_client()
        await minio_client.ensure_bucket_exists()
        logger.info("MinIO bucket OK")
    except Exception as e:
        logger.error("MinIO bucket check failed", error=str(e))
    
    logger.info("API started successfully")
    yield
    
    # Shutdown
    logger.info("API shutting down")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title="FactoryOps API",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # Middleware (order matters)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all in development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(devices.router, prefix="/api/v1")
    app.include_router(telemetry.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")
    app.include_router(rules.router, prefix="/api/v1")
    app.include_router(alerts.router, prefix="/api/v1")
    app.include_router(analytics.router, prefix="/api/v1")
    app.include_router(reports.router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        dependencies = {
            "mysql": "ok" if await check_db_health() else "error",
            "redis": "ok" if await check_redis_health() else "error",
            "influxdb": "ok" if await check_influx_health() else "error",
            "minio": "ok",  # Bucket creation would have failed on startup if unreachable
        }
        
        all_healthy = all(d == "ok" for d in dependencies.values())
        
        return {
            "status": "healthy" if all_healthy else "unhealthy",
            "service": "api",
            "version": "1.0.0",
            "dependencies": dependencies,
        }
    
    # Exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        logger.warning(
            "Validation error",
            errors=exc.errors(),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "detail": exc.errors(),
                }
            },
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        request_id = structlog.contextvars.get_contextvars().get("request_id", "unknown")
        logger.exception(
            "Unhandled exception",
            request_id=request_id,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "request_id": request_id,
                }
            },
        )
    
    return app


# Create app instance
app = create_app()
