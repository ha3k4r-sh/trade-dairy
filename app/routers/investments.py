from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.models import User, Investment, Withdrawal
from app.auth import get_current_user

router = APIRouter(tags=["investments"])

class InvestmentCreate(BaseModel):
    type: str
    amount: float
    source: str
    date: str
    notes: Optional[str] = None

class InvestmentUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = None
    source: Optional[str] = None
    date: Optional[str] = None
    notes: Optional[str] = None

class WithdrawalCreate(BaseModel):
    amount: float
    date: str
    reason: Optional[str] = None

@router.get("/api/investments")
async def get_investments(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investments = db.query(Investment).filter(Investment.user_id == user.id).order_by(Investment.date.desc()).all()
    return [
        {
            "id": i.id,
            "type": i.type,
            "amount": i.amount,
            "source": i.source,
            "date": i.date.isoformat(),
            "notes": i.notes,
            "created_at": i.created_at.isoformat()
        }
        for i in investments
    ]

@router.post("/api/investments")
async def create_investment(
    data: InvestmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investment = Investment(
        user_id=user.id,
        type=data.type,
        amount=data.amount,
        source=data.source,
        date=datetime.fromisoformat(data.date),
        notes=data.notes
    )
    db.add(investment)
    db.commit()
    db.refresh(investment)
    return {
        "id": investment.id,
        "type": investment.type,
        "amount": investment.amount,
        "source": investment.source,
        "date": investment.date.isoformat(),
        "notes": investment.notes
    }

@router.get("/api/investments/withdrawals")
async def get_withdrawals(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    withdrawals = db.query(Withdrawal).filter(Withdrawal.user_id == user.id).order_by(Withdrawal.date.desc()).all()
    return [
        {
            "id": w.id,
            "amount": w.amount,
            "reason": w.reason,
            "date": w.date.isoformat(),
            "created_at": w.created_at.isoformat()
        }
        for w in withdrawals
    ]

@router.post("/api/investments/withdrawals")
async def create_withdrawal(
    data: WithdrawalCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    withdrawal = Withdrawal(
        user_id=user.id,
        amount=data.amount,
        reason=data.reason,
        date=datetime.fromisoformat(data.date)
    )
    db.add(withdrawal)
    db.commit()
    db.refresh(withdrawal)
    return {
        "id": withdrawal.id,
        "amount": withdrawal.amount,
        "reason": withdrawal.reason,
        "date": withdrawal.date.isoformat()
    }

@router.delete("/api/investments/withdrawals/{withdrawal_id}")
async def delete_withdrawal(
    withdrawal_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    withdrawal = db.query(Withdrawal).filter(Withdrawal.id == withdrawal_id, Withdrawal.user_id == user.id).first()
    if not withdrawal:
        raise HTTPException(status_code=404, detail="Withdrawal not found")
    db.delete(withdrawal)
    db.commit()
    return {"message": "Withdrawal deleted"}

@router.get("/api/investments/{investment_id}")
async def get_investment(
    investment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investment = db.query(Investment).filter(Investment.id == investment_id, Investment.user_id == user.id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    return {
        "id": investment.id,
        "type": investment.type,
        "amount": investment.amount,
        "source": investment.source,
        "date": investment.date.isoformat(),
        "notes": investment.notes,
        "created_at": investment.created_at.isoformat()
    }

@router.patch("/api/investments/{investment_id}")
async def update_investment(
    investment_id: int,
    data: InvestmentUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investment = db.query(Investment).filter(Investment.id == investment_id, Investment.user_id == user.id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    
    if data.type is not None:
        investment.type = data.type
    if data.amount is not None:
        investment.amount = data.amount
    if data.source is not None:
        investment.source = data.source
    if data.date is not None:
        investment.date = datetime.fromisoformat(data.date)
    if data.notes is not None:
        investment.notes = data.notes
    
    db.commit()
    db.refresh(investment)
    return {
        "id": investment.id,
        "type": investment.type,
        "amount": investment.amount,
        "source": investment.source,
        "date": investment.date.isoformat(),
        "notes": investment.notes
    }

@router.delete("/api/investments/{investment_id}")
async def delete_investment(
    investment_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    investment = db.query(Investment).filter(Investment.id == investment_id, Investment.user_id == user.id).first()
    if not investment:
        raise HTTPException(status_code=404, detail="Investment not found")
    db.delete(investment)
    db.commit()
    return {"message": "Investment deleted"}
