from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, config, ingest, mistakes, meta_agent

app = FastAPI(title="Customer Service AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(config.router)
app.include_router(ingest.router)
app.include_router(mistakes.router)
app.include_router(meta_agent.router)

@app.get("/")
def root():
    return {"message": "Welcome to the Customer Service AI Backend!"}
