from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.models import User, PlanTrade
from app.auth import get_current_user

router = APIRouter(prefix="/api/plan", tags=["plan"])

@router.get("")
async def get_plan(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    plan_trades = db.query(PlanTrade).order_by(PlanTrade.trade_number.asc()).all()
    return [
        {
            "trade_number": p.trade_number,
            "initial_investment": p.initial_investment,
            "profit_percent": p.profit_percent,
            "after_trade_close": p.after_trade_close,
            "no_of_lots": p.no_of_lots,
            "capital_used": p.capital_used
        }
        for p in plan_trades
    ]
