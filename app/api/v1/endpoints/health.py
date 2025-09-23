from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    return {"status": "healthy", "service": "commute-ai-backend", "version": "0.1.0"}
