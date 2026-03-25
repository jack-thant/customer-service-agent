from fastapi import APIRouter

router = APIRouter(prefix="/mistakes", tags=["mistakes"])

@router.get("")
def list_mistakes():
    return {"message": "mistakes list"}