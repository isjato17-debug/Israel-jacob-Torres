"""Owner-only offline financial-control console. No endpoint can activate paid providers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import User
from ..security import require_csrf, ensure_not_lockdown
from ..services import ai_finance as costs
from .growth import platform_owner
from .documents import owned

router = APIRouter(prefix="/api/v2/operator/ai-finance", tags=["Owner AI financial protection"])


@router.get("")
def get(user: User = Depends(platform_owner), db: Session = Depends(get_db)):
    return costs.describe(db)


@router.put("")
def configure(data: costs.PolicyInput, user: User = Depends(platform_owner),
              db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    try:
        costs.configure(db, user, data)
        db.commit()
    except HTTPException as exc:
        db.rollback()
        costs.event(db, user, "ai_financial_configuration_denied", "global", code=exc.status_code)
        db.commit()
        raise
    return costs.describe(db)


def receipt(r):
    return {"id":r.id, "status":r.status, "maximum_microusd":r.maximum_microusd,
            "actual_microusd":r.actual_microusd, "mode":costs.MODE, "actual_external_cost_microusd":0}


@router.post("/reservations/{project_id}")
def reserve(project_id: str, data: costs.Reserve, user: User = Depends(platform_owner),
            db: Session = Depends(get_db), _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    r = costs.reserve(db, user, owned(db, user, project_id), data)
    db.commit()
    return receipt(r)


@router.post("/reconcile/{reservation_id}")
def reconcile(reservation_id: str, data: costs.Usage | None = None,
              user: User = Depends(platform_owner), db: Session = Depends(get_db),
              _: bool = Depends(require_csrf)):
    ensure_not_lockdown(db, user)
    r = costs.reconcile(db, user, reservation_id, data)
    db.commit()
    return receipt(r)
