"""
Main FastAPI application for Automated Email Quote System
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from app.routers import emails, quotes, customers, products, wix, businesses, oauth
from app.database import engine, Base
from app.config import settings
from app.services.scheduler_service import start_scheduler, stop_scheduler

# In development, create tables if they don't exist
# In production, use Alembic migrations instead
if settings.DEBUG:
    Base.metadata.create_all(bind=engine)
else:
    # In production, run migrations on startup
    # This is handled by the deployment platform or startup script
    pass

app = FastAPI(
    title="Automated Email Quote System",
    description="AI-powered email-to-quote system for Kyoto Custom Surfaces",
    version="1.0.0"
)

# CORS middleware for Wix integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(oauth.router, prefix="/api/oauth/google", tags=["oauth"])
app.include_router(businesses.router, prefix="/api/businesses", tags=["businesses"])
app.include_router(emails.router, prefix="/api/emails", tags=["emails"])
app.include_router(quotes.router, prefix="/api/quotes", tags=["quotes"])
app.include_router(customers.router, prefix="/api/customers", tags=["customers"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(wix.router, prefix="/api/wix", tags=["wix"])


@app.get("/")
async def root():
    return {
        "message": "Automated Email Quote System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for deployment platforms
    
    Returns:
        - Database connectivity status
        - Scheduler status
        - API status
    """
    from sqlalchemy import text
    from app.database import SessionLocal
    
    health_status = {
        "status": "healthy",
        "version": "1.0.0",
        "services": {}
    }
    
    # Check database connectivity
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = f"error: {str(e)}"
    
    # Check scheduler status
    try:
        from app.services.scheduler_service import scheduler
        if scheduler.running:
            health_status["services"]["scheduler"] = "running"
        else:
            health_status["services"]["scheduler"] = "stopped"
    except Exception as e:
        health_status["services"]["scheduler"] = f"error: {str(e)}"
    
    return health_status


@app.on_event("startup")
async def startup_event():
    """Start background services on app startup"""
    start_scheduler()


@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services on app shutdown"""
    stop_scheduler()


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


