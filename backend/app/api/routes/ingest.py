from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, HttpUrl

from app.services.ingest_service import KBIngestService

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestCategoryRequest(BaseModel):
    url: HttpUrl
    force_reingest: bool = False


@router.post("/category")
def ingest_category(req: IngestCategoryRequest):
    service = KBIngestService()

    try:
        result = service.ingest_category(
            str(req.url),
            force_reingest=req.force_reingest,
        )
        return {
            "status": "success",
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
  
## temporily added for debugging  
@router.get("/debug/search")
def debug_search(q: str):
    service = KBIngestService()
    query_embedding = service._embed_texts([q])[0]
    result = service.collection.query(
        query_embeddings=[query_embedding],
        n_results=3,
    )
    return result