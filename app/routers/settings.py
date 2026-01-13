from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.models import User, Settings
from app.auth import get_current_user

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingsUpdate(BaseModel):
    initial_capital: Optional[float] = None
    target_capital: Optional[float] = None
    return_per_trade: Optional[float] = None
    reserve_amount: Optional[float] = None
    nifty_lot_size: Optional[int] = None
    banknifty_lot_size: Optional[int] = None
    finnifty_lot_size: Optional[int] = None
    nifty_expiry_day: Optional[str] = None

@router.get("")
async def get_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = db.query(Settings).filter(Settings.user_id == user.id).first()
    if not settings:
        settings = Settings(
            user_id=user.id,
            initial_capital=40000,
            target_capital=10000000,
            return_per_trade=4,
            reserve_amount=170000,
            nifty_lot_size=65,
            banknifty_lot_size=30,
            finnifty_lot_size=60,
            nifty_expiry_day="TUESDAY"
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    
    return {
        "initial_capital": settings.initial_capital,
        "target_capital": settings.target_capital,
        "return_per_trade": settings.return_per_trade,
        "reserve_amount": settings.reserve_amount,
        "nifty_lot_size": settings.nifty_lot_size or 65,
        "banknifty_lot_size": settings.banknifty_lot_size or 30,
        "finnifty_lot_size": settings.finnifty_lot_size or 60,
        "nifty_expiry_day": settings.nifty_expiry_day or "TUESDAY"
    }

@router.patch("")
async def update_settings(
    data: SettingsUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = db.query(Settings).filter(Settings.user_id == user.id).first()
    if not settings:
        settings = Settings(user_id=user.id)
        db.add(settings)
    
    if data.initial_capital is not None:
        settings.initial_capital = data.initial_capital
    if data.target_capital is not None:
        settings.target_capital = data.target_capital
    if data.return_per_trade is not None:
        settings.return_per_trade = data.return_per_trade
    if data.reserve_amount is not None:
        settings.reserve_amount = data.reserve_amount
    if data.nifty_lot_size is not None:
        settings.nifty_lot_size = data.nifty_lot_size
    if data.banknifty_lot_size is not None:
        settings.banknifty_lot_size = data.banknifty_lot_size
    if data.finnifty_lot_size is not None:
        settings.finnifty_lot_size = data.finnifty_lot_size
    if data.nifty_expiry_day is not None:
        settings.nifty_expiry_day = data.nifty_expiry_day
    
    db.commit()
    db.refresh(settings)
    return {
        "initial_capital": settings.initial_capital,
        "target_capital": settings.target_capital,
        "return_per_trade": settings.return_per_trade,
        "reserve_amount": settings.reserve_amount,
        "nifty_lot_size": settings.nifty_lot_size or 65,
        "banknifty_lot_size": settings.banknifty_lot_size or 30,
        "finnifty_lot_size": settings.finnifty_lot_size or 60,
        "nifty_expiry_day": settings.nifty_expiry_day or "TUESDAY"
    }
