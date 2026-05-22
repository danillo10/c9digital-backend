from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from app.core.database import get_db
from app.models.campaign import Campaign, Task, TaskComment, CampaignStatus, TaskStatus
from app.models.client import Client
from app.models.user import User
from app.schemas.campaign import (
    CampaignCreate, CampaignUpdate, CampaignResponse,
    TaskCreate, TaskUpdate, TaskResponse, TaskDetailResponse,
    TaskCommentCreate, TaskCommentResponse
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


def verify_client_ownership(client_id: int, user: User, db: Session):
    client = db.query(Client).filter(Client.id == client_id, Client.owner_id == user.id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


def get_task_or_404(task_id: int, user: User, db: Session) -> Task:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    verify_client_ownership(task.client_id, user, db)
    return task


def build_task_detail(task: Task) -> dict:
    comments = []
    for c in task.comments:
        comments.append({
            "id": c.id,
            "task_id": c.task_id,
            "user_id": c.user_id,
            "content": c.content,
            "is_activity": c.is_activity,
            "activity_type": c.activity_type,
            "created_at": c.created_at,
            "user_name": c.user.name if c.user else None,
        })
    return {
        "id": task.id,
        "client_id": task.client_id,
        "title": task.title,
        "description": task.description,
        "status": task.status,
        "priority": task.priority,
        "due_date": task.due_date,
        "completed_at": task.completed_at,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
        "comments": comments,
    }


# ─── Campaigns ───────────────────────────────────────────────────────────────

@router.get("/", response_model=List[CampaignResponse])
def list_campaigns(
    client_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client_ids = [c.id for c in db.query(Client).filter(Client.owner_id == current_user.id).all()]
    query = db.query(Campaign).filter(Campaign.client_id.in_(client_ids))
    if client_id:
        query = query.filter(Campaign.client_id == client_id)
    return query.order_by(Campaign.created_at.desc()).all()


@router.post("/", response_model=CampaignResponse, status_code=201)
def create_campaign(
    campaign_data: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_client_ownership(campaign_data.client_id, current_user, db)
    campaign = Campaign(**campaign_data.model_dump())
    db.add(campaign)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: int,
    campaign_update: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    verify_client_ownership(campaign.client_id, current_user, db)

    for key, value in campaign_update.model_dump(exclude_unset=True).items():
        setattr(campaign, key, value)
    db.commit()
    db.refresh(campaign)
    return campaign


@router.delete("/{campaign_id}", status_code=204)
def delete_campaign(
    campaign_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campanha não encontrada")
    verify_client_ownership(campaign.client_id, current_user, db)
    db.delete(campaign)
    db.commit()


# ─── Tasks ────────────────────────────────────────────────────────────────────

@router.get("/tasks/", response_model=List[TaskResponse])
def list_tasks(
    client_id: Optional[int] = None,
    status: Optional[TaskStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client_ids = [c.id for c in db.query(Client).filter(Client.owner_id == current_user.id).all()]
    query = db.query(Task).filter(Task.client_id.in_(client_ids))
    if client_id:
        query = query.filter(Task.client_id == client_id)
    if status:
        query = query.filter(Task.status == status)
    return query.order_by(Task.updated_at.desc()).all()


@router.post("/tasks/", response_model=TaskResponse, status_code=201)
def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    verify_client_ownership(task_data.client_id, current_user, db)
    task = Task(**task_data.model_dump())
    db.add(task)
    db.flush()

    opening = TaskComment(
        task_id=task.id,
        user_id=current_user.id,
        content=f"Demanda criada.",
        is_activity=True,
        activity_type="created",
    )
    db.add(opening)
    db.commit()
    db.refresh(task)
    return task


@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = get_task_or_404(task_id, current_user, db)
    return build_task_detail(task)


@router.put("/tasks/{task_id}", response_model=TaskDetailResponse)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = get_task_or_404(task_id, current_user, db)

    status_labels = {
        "todo": "A Fazer", "in_progress": "Em Progresso",
        "review": "Em Revisão", "done": "Concluída"
    }
    priority_labels = {
        "low": "Baixa", "medium": "Média", "high": "Alta", "urgent": "Urgente"
    }

    activity_entries = []

    if task_update.status and task_update.status != task.status:
        old_label = status_labels.get(task.status, task.status)
        new_label = status_labels.get(task_update.status, task_update.status)
        activity_entries.append(TaskComment(
            task_id=task.id,
            user_id=current_user.id,
            content=f"Status alterado de **{old_label}** para **{new_label}**.",
            is_activity=True,
            activity_type="status_change",
        ))
        if task_update.status == TaskStatus.DONE and not task.completed_at:
            task.completed_at = datetime.utcnow()

    if task_update.priority and task_update.priority != task.priority:
        old_label = priority_labels.get(task.priority, task.priority)
        new_label = priority_labels.get(task_update.priority, task_update.priority)
        activity_entries.append(TaskComment(
            task_id=task.id,
            user_id=current_user.id,
            content=f"Prioridade alterada de **{old_label}** para **{new_label}**.",
            is_activity=True,
            activity_type="priority_change",
        ))

    if task_update.due_date and task_update.due_date != task.due_date:
        activity_entries.append(TaskComment(
            task_id=task.id,
            user_id=current_user.id,
            content=f"Prazo definido para **{task_update.due_date.strftime('%d/%m/%Y')}**.",
            is_activity=True,
            activity_type="due_date_change",
        ))

    for key, value in task_update.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    task.updated_at = datetime.utcnow()

    for entry in activity_entries:
        db.add(entry)

    db.commit()
    db.refresh(task)
    return build_task_detail(task)


@router.delete("/tasks/{task_id}", status_code=204)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = get_task_or_404(task_id, current_user, db)
    db.delete(task)
    db.commit()


# ─── Task Comments ────────────────────────────────────────────────────────────

@router.post("/tasks/{task_id}/comments", response_model=TaskCommentResponse, status_code=201)
def add_comment(
    task_id: int,
    comment_data: TaskCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = get_task_or_404(task_id, current_user, db)

    comment = TaskComment(
        task_id=task_id,
        user_id=current_user.id,
        content=comment_data.content,
        is_activity=False,
    )
    db.add(comment)
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)

    return {
        "id": comment.id,
        "task_id": comment.task_id,
        "user_id": comment.user_id,
        "content": comment.content,
        "is_activity": comment.is_activity,
        "activity_type": comment.activity_type,
        "created_at": comment.created_at,
        "user_name": current_user.name,
    }


@router.delete("/tasks/{task_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    task_id: int,
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    get_task_or_404(task_id, current_user, db)
    comment = db.query(TaskComment).filter(
        TaskComment.id == comment_id,
        TaskComment.task_id == task_id,
        TaskComment.user_id == current_user.id,
        TaskComment.is_activity == False
    ).first()
    if not comment:
        raise HTTPException(status_code=404, detail="Comentário não encontrado")
    db.delete(comment)
    db.commit()
