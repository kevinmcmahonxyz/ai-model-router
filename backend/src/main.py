"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

# Create FastAPI app
app = FastAPI(
    title="AI Model Router",
    description="Route LLM requests with cost tracking and observability",
    version="0.1.0"
)

# Add CORS middleware (for frontend later)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Model Router API",
        "version": "0.1.0",
        "docs": "/docs"
    }