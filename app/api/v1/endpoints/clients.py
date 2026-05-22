from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.client import Client, ClientStatus
from app.models.user import User
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/", response_model=List[ClientResponse])
def list_clients(
    status: Optional[ClientStatus] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Client).filter(Client.owner_id == current_user.id)
    if status:
        query = query.filter(Client.status == status)
    return query.offset(skip).limit(limit).all()


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = Client(**client_data.model_dump(), owner_id=current_user.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id, Client.owner_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    client_update: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id, Client.owner_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    for key, value in client_update.model_dump(exclude_unset=True).items():
        setattr(client, key, value)
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client = db.query(Client).filter(Client.id == client_id, Client.owner_id == current_user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    db.delete(client)
    db.commit()
