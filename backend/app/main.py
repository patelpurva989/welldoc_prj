"""FDA Regulatory Automation Platform - Main Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings
from .core.database import engine, Base
from .api import regulatory, auth
from .api import documents as documents_api
from .api import reviews as reviews_api
from .api import admin as admin_api
from sqlalchemy import text

# Import models so SQLAlchemy registers them before create_all
from .models import fda_knowledge  # noqa: F401  (registers FDAKnowledgeBase table)

# Create database tables (includes all new models)
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-powered FDA regulatory submission automation platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(regulatory.router)
app.include_router(auth.router)
app.include_router(documents_api.router)
app.include_router(reviews_api.router)
app.include_router(admin_api.router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FDA Regulatory Automation Platform",
        "version": settings.VERSION,
        "docs": "/api/docs"
    }


@app.get("/health")
async def health_check():
    """Health check — includes DB and AI configuration status."""
    from .core.database import SessionLocal
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "version": settings.VERSION,
        "database": db_status,
        "ai_configured": bool(settings.ANTHROPIC_API_KEY),
        "features": {
            "rag": True,
            "streaming": True,
            "auth": True,
            "document_analysis": True,
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8400,
        reload=settings.DEBUG
    )
