from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.models.client import Client, ClientStatus
from app.models.campaign import Campaign, CampaignStatus, Task, TaskStatus
from app.models.social import SocialAccount, SocialPost, PostStatus
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    client_ids = [c.id for c in db.query(Client).filter(Client.owner_id == current_user.id).all()]

    total_clients = db.query(Client).filter(Client.owner_id == current_user.id).count()
    active_clients = db.query(Client).filter(
        Client.owner_id == current_user.id,
        Client.status == ClientStatus.ACTIVE
    ).count()

    active_campaigns = db.query(Campaign).filter(
        Campaign.client_id.in_(client_ids),
        Campaign.status == CampaignStatus.ACTIVE
    ).count() if client_ids else 0

    pending_tasks = db.query(Task).filter(
        Task.client_id.in_(client_ids),
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
    ).count() if client_ids else 0

    social_accounts = db.query(SocialAccount).filter(
        SocialAccount.client_id.in_(client_ids)
    ).count() if client_ids else 0

    scheduled_posts = db.query(SocialPost).join(SocialAccount).filter(
        SocialAccount.client_id.in_(client_ids),
        SocialPost.status == PostStatus.SCHEDULED
    ).count() if client_ids else 0

    total_followers = db.query(SocialAccount).filter(
        SocialAccount.client_id.in_(client_ids)
    ).with_entities(
        SocialAccount.followers_count
    ).all() if client_ids else []
    total_followers_count = sum(f[0] for f in total_followers)

    recent_clients = db.query(Client).filter(
        Client.owner_id == current_user.id
    ).order_by(Client.created_at.desc()).limit(5).all()

    return {
        "total_clients": total_clients,
        "active_clients": active_clients,
        "active_campaigns": active_campaigns,
        "pending_tasks": pending_tasks,
        "social_accounts": social_accounts,
        "scheduled_posts": scheduled_posts,
        "total_followers": total_followers_count,
        "recent_clients": [
            {
                "id": c.id,
                "name": c.name,
                "company": c.company,
                "status": c.status,
                "industry": c.industry,
            }
            for c in recent_clients
        ]
    }
