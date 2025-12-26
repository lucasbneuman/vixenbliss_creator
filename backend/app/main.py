from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

from app.database import engine, get_db, Base
from app.models import Avatar, User, IdentityComponent, ContentPiece

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="VixenBliss Creator API",
    description="AI Avatar Management Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "VixenBliss Creator API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connection
        db.execute("SELECT 1")
        return {
            "status": "healthy",
            "database": "connected",
            "version": "1.0.0"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

# API Routes
from app.api import identities, storage, loras, costs, content

app.include_router(identities.router)
app.include_router(storage.router)
app.include_router(loras.router)
app.include_router(costs.router)
app.include_router(content.router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
