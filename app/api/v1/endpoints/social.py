from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.social import SocialAccount, SocialPost, PostStatus
from app.models.client import Client
from app.models.user import User
from app.schemas.social import (
    SocialAccountCreate, SocialAccountUpdate, SocialAccountResponse,
    SocialPostCreate, SocialPostUpdate, SocialPostResponse
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


def verify_client_ownership(client_id: int, user: User, db: Session):
    client = db.query(Client).filter(Client.id == client_id, Client.owner_id == user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.get("/accounts/{client_id}", response_model=List[SocialAccountResponse])
def list_social_accounts(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_client_ownership(client_id, current_user, db)
    return db.query(SocialAccount).filter(SocialAccount.client_id == client_id).all()


@router.post("/accounts", response_model=SocialAccountResponse, status_code=201)
def create_social_account(
    account_data: SocialAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_client_ownership(account_data.client_id, current_user, db)
    account = SocialAccount(**account_data.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.put("/accounts/{account_id}", response_model=SocialAccountResponse)
def update_social_account(
    account_id: int,
    account_update: SocialAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    verify_client_ownership(account.client_id, current_user, db)

    for key, value in account_update.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account


@router.delete("/accounts/{account_id}", status_code=204)
def delete_social_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    verify_client_ownership(account.client_id, current_user, db)
    db.delete(account)
    db.commit()


@router.get("/posts/{account_id}", response_model=List[SocialPostResponse])
def list_posts(
    account_id: int,
    status: Optional[PostStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    verify_client_ownership(account.client_id, current_user, db)

    query = db.query(SocialPost).filter(SocialPost.account_id == account_id)
    if status:
        query = query.filter(SocialPost.status == status)
    return query.order_by(SocialPost.created_at.desc()).all()


@router.post("/posts", response_model=SocialPostResponse, status_code=201)
def create_post(
    post_data: SocialPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = db.query(SocialAccount).filter(SocialAccount.id == post_data.account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Conta não encontrada")
    verify_client_ownership(account.client_id, current_user, db)

    post = SocialPost(**post_data.model_dump())
    if post.scheduled_at:
        post.status = PostStatus.SCHEDULED
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


@router.put("/posts/{post_id}", response_model=SocialPostResponse)
def update_post(
    post_id: int,
    post_update: SocialPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")

    for key, value in post_update.model_dump(exclude_unset=True).items():
        setattr(post, key, value)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/posts/{post_id}", status_code=204)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    post = db.query(SocialPost).filter(SocialPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post não encontrado")
    db.delete(post)
    db.commit()
