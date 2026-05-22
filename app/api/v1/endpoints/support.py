from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import random
import string
from app.core.database import get_db
from app.models.support import Ticket, TicketMessage, TicketStatus, MessageSender
from app.models.user import User
from app.schemas.support import (
    TicketCreate, TicketUpdate, TicketListResponse, TicketDetailResponse,
    TicketMessageCreate, TicketMessageResponse
)
from app.api.v1.endpoints.auth import get_current_user

router = APIRouter()


def generate_ticket_number() -> str:
    suffix = ''.join(random.choices(string.digits, k=6))
    return f"C9-{suffix}"


def build_ticket_list_response(ticket: Ticket, db: Session) -> dict:
    message_count = db.query(func.count(TicketMessage.id)).filter(
        TicketMessage.ticket_id == ticket.id
    ).scalar() or 0

    last_msg = db.query(TicketMessage).filter(
        TicketMessage.ticket_id == ticket.id
    ).order_by(TicketMessage.created_at.desc()).first()

    return {
        "id": ticket.id,
        "user_id": ticket.user_id,
        "ticket_number": ticket.ticket_number,
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
        "priority": ticket.priority,
        "category": ticket.category,
        "is_read_by_user": ticket.is_read_by_user,
        "created_at": ticket.created_at,
        "updated_at": ticket.updated_at,
        "message_count": message_count,
        "last_message_at": last_msg.created_at if last_msg else None,
    }


@router.get("/", response_model=List[TicketListResponse])
def list_tickets(
    status: Optional[TicketStatus] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Ticket).filter(Ticket.user_id == current_user.id)
    if status:
        query = query.filter(Ticket.status == status)
    tickets = query.order_by(Ticket.updated_at.desc()).all()
    return [build_ticket_list_response(t, db) for t in tickets]


@router.post("/", response_model=TicketDetailResponse, status_code=201)
def create_ticket(
    ticket_data: TicketCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket_number = generate_ticket_number()
    while db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first():
        ticket_number = generate_ticket_number()

    ticket = Ticket(
        user_id=current_user.id,
        ticket_number=ticket_number,
        title=ticket_data.title,
        description=ticket_data.description,
        priority=ticket_data.priority,
        category=ticket_data.category,
    )
    db.add(ticket)
    db.flush()

    first_message = TicketMessage(
        ticket_id=ticket.id,
        sender=MessageSender.USER,
        content=ticket_data.description,
    )
    db.add(first_message)

    auto_reply = TicketMessage(
        ticket_id=ticket.id,
        sender=MessageSender.SUPPORT,
        content=(
            f"Olá, {current_user.name.split()[0]}! 👋\n\n"
            f"Recebemos seu chamado **#{ticket_number}** e nossa equipe já foi notificada. "
            f"Em breve um especialista irá analisar sua solicitação e retornar com uma resposta.\n\n"
            f"⏱ Tempo médio de resposta: **2 horas úteis**\n\n"
            f"Caso tenha mais informações para compartilhar, basta responder aqui neste chamado."
        ),
    )
    db.add(auto_reply)
    db.commit()
    db.refresh(ticket)

    result = build_ticket_list_response(ticket, db)
    result["messages"] = ticket.messages
    result["resolved_at"] = ticket.resolved_at
    return result


@router.get("/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id, Ticket.user_id == current_user.id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    ticket.is_read_by_user = True
    db.commit()
    db.refresh(ticket)

    result = build_ticket_list_response(ticket, db)
    result["messages"] = ticket.messages
    result["resolved_at"] = ticket.resolved_at
    return result


@router.post("/{ticket_id}/messages", response_model=TicketMessageResponse, status_code=201)
def add_message(
    ticket_id: int,
    message_data: TicketMessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id, Ticket.user_id == current_user.id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if ticket.status == TicketStatus.CLOSED:
        raise HTTPException(status_code=400, detail="Chamado encerrado. Abra um novo chamado.")

    if ticket.status == TicketStatus.RESOLVED:
        ticket.status = TicketStatus.OPEN

    message = TicketMessage(
        ticket_id=ticket_id,
        sender=MessageSender.USER,
        content=message_data.content,
    )
    db.add(message)
    ticket.is_read_by_support = False
    ticket.is_read_by_user = True
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(message)
    return message


@router.put("/{ticket_id}", response_model=TicketListResponse)
def update_ticket(
    ticket_id: int,
    ticket_update: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id, Ticket.user_id == current_user.id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    if ticket_update.status:
        ticket.status = ticket_update.status
        if ticket_update.status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()

    if ticket_update.priority:
        ticket.priority = ticket_update.priority

    db.commit()
    db.refresh(ticket)
    return build_ticket_list_response(ticket, db)


@router.delete("/{ticket_id}", status_code=204)
def close_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id, Ticket.user_id == current_user.id
    ).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")

    ticket.status = TicketStatus.CLOSED
    db.commit()
