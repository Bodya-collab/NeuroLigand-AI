from fastapi import FastAPI
from app.api import routes
from app.database import engine, Base
from app import models

# Create database tables based on our models
models.Base.metadata.create_all(bind=engine)

# Init FastAPI application
app = FastAPI(
    title="NeuroLigand Core API",
    description="Backend for AI-driven Molecular Docking",
    version="1.0.0",
)

# Endpoints for our API are defined in routes.py, we include them here
app.include_router(routes.router, prefix="/api/v1")


@app.get("/")
def health_check():
    """Verify that the API is running and responsive."""
    return {"status": "Online", "system": "NeuroLigand Backend v1.0"}
