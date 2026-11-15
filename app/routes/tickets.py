from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.categories import CATEGORIES
from app.config import settings
from app.database.db import get_db, store_ticket
from app.schemas.tickets import TicketCreate, TicketResponse
from app.services.classifier import InvalidCategoryError, classify_ticket
from app.services.ollama_client import OllamaError
from app.services.cascade import classify_with_cascade

router = APIRouter()


@router.post("/tickets", response_model=TicketResponse, status_code=201)
def submit_ticket(payload: TicketCreate, request: Request, db: Session = Depends(get_db)):
    try:
        if settings.classification_mode == "single":
            category = classify_ticket(payload.narrative)
            request.state.first_model = settings.ollama_model
            request.state.final_model = settings.ollama_model
            request.state.escalated = False
            request.state.escalation_setting = None
        elif settings.classification_mode == "cascade":
            result = classify_with_cascade(payload.narrative, request=request)
            category = result.category
        else:
            raise InvalidCategoryError("Unknown classification mode")
        if category not in CATEGORIES:
            raise InvalidCategoryError("Classifier returned an invalid category")
    except (InvalidCategoryError, OllamaError) as exc:
        request.state.error = type(exc).__name__
        raise HTTPException(status_code=502, detail="Ticket classification failed") from exc
    request.state.predicted_category = category
    ticket = store_ticket(db, payload.narrative, category, request.state.final_model)
    request.state.ticket_id = ticket.id
    return ticket
