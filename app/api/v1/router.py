from fastapi import APIRouter
from app.api.v1.endpoints import auth, clients, social, campaigns, dashboard, support

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clientes"])
api_router.include_router(social.router, prefix="/social", tags=["Redes Sociais"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["Campanhas"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(support.router, prefix="/support", tags=["Suporte"])
