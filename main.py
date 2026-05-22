from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
import app.models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="C9Digital API",
    description="Plataforma SaaS de Marketing Digital",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "C9Digital API - Marketing Digital SaaS", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
