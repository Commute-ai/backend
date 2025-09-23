from fastapi import FastAPI

from app.api.v1.api import api_router

app = FastAPI(
    title="Commute.ai API",
    description="AI-powered public transport routing",
    version="0.1.0",
)


@app.get("/")
def read_root():
    return {"message": "Welcome to Commute.ai API"}


# Include API v1 router
app.include_router(api_router, prefix="/api/v1")
