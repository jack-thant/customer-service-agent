from fastapi import APIRouter

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("")
def ingest():
    return {"message": "ingest triggered"}