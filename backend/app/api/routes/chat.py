from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str


@router.post("")
def chat(req: ChatRequest):
    return {
        "response": f"You said: {req.message}"
    }