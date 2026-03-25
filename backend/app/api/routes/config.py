from fastapi import APIRouter

router = APIRouter(prefix="/config", tags=["config"])

@router.get("")
def get_config():
    return  {"message": "Config endpoint"}