from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import cases, metrics, webhooks
from app.db.session import engine
from app.db import models

from app.db.init_db import init_db

# Initialize database schema and run hackathon migrations
init_db()

app = FastAPI(title="PayProof AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cases.router)
app.include_router(metrics.router)
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
