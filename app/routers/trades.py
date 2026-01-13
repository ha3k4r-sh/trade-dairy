from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.database import get_db
from app.models.models import User, Trade, TradeEntry
from app.auth import get_current_user

router = APIRouter(prefix="/api/trades", tags=["trades"])

class EntryCreate(BaseModel):
    price: float
    lots: int
    quantity: int

class TradeCreate(BaseModel):
    symbol: str
    instrument_type: str
    lot_size: int
    entries: List[EntryCreate]

class TradeClose(BaseModel):
    exit_price: float
    against_trend: bool = False
    outcome: Optional[str] = None
    learnings: Optional[str] = None
    feedback: Optional[str] = None
    screenshot: Optional[str] = None

class TradeUpdate(BaseModel):
    against_trend: Optional[bool] = None
    learnings: Optional[str] = None
    feedback: Optional[str] = None
    screenshot: Optional[str] = None
    exit_price: Optional[float] = None
    outcome: Optional[str] = None

class AddEntry(BaseModel):
    price: float
    lots: int

@router.get("")
async def get_trades(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trades = db.query(Trade).filter(Trade.user_id == user.id).order_by(Trade.created_at.desc()).all()
    return [serialize_trade(t) for t in trades]

@router.get("/{trade_id}")
async def get_trade(
    trade_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return serialize_trade(trade)

@router.post("")
async def create_trade(
    data: TradeCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trade_count = db.query(Trade).filter(Trade.user_id == user.id).count()
    trade_number = trade_count + 1
    
    # Calculate average price
    total_value = sum(e.price * e.quantity for e in data.entries)
    total_qty = sum(e.quantity for e in data.entries)
    avg_price = total_value / total_qty if total_qty > 0 else 0
    
    trade = Trade(
        user_id=user.id,
        trade_number=trade_number,
        symbol=data.symbol.upper(),
        instrument_type=data.instrument_type,
        lot_size=data.lot_size,
        avg_price=avg_price,
        status="OPEN"
    )
    db.add(trade)
    db.flush()
    
    for entry in data.entries:
        db.add(TradeEntry(
            trade_id=trade.id,
            price=entry.price,
            lots=entry.lots,
            quantity=entry.quantity
        ))
    
    db.commit()
    db.refresh(trade)
    return serialize_trade(trade)

@router.post("/{trade_id}/entries")
async def add_entry(
    trade_id: int,
    data: AddEntry,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != "OPEN":
        raise HTTPException(status_code=400, detail="Cannot add entry to closed trade")
    
    quantity = data.lots * trade.lot_size
    db.add(TradeEntry(
        trade_id=trade.id,
        price=data.price,
        lots=data.lots,
        quantity=quantity
    ))
    
    # Recalculate average
    entries = db.query(TradeEntry).filter(TradeEntry.trade_id == trade.id).all()
    total_value = sum(e.price * e.quantity for e in entries) + (data.price * quantity)
    total_qty = sum(e.quantity for e in entries) + quantity
    trade.avg_price = total_value / total_qty if total_qty > 0 else 0
    
    db.commit()
    db.refresh(trade)
    return serialize_trade(trade)

@router.post("/{trade_id}/close")
async def close_trade(
    trade_id: int,
    data: TradeClose,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != "OPEN":
        raise HTTPException(status_code=400, detail="Trade is already closed")
    
    total_qty = sum(e.quantity for e in trade.entries)
    avg_price = trade.avg_price or 0
    
    return_amount = (data.exit_price - avg_price) * total_qty
    return_percent = ((data.exit_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
    
    trade.exit_price = data.exit_price
    trade.exit_datetime = datetime.utcnow()
    trade.return_amount = return_amount
    trade.return_percent = return_percent
    trade.status = "CLOSED"
    trade.against_trend = data.against_trend
    trade.outcome = data.outcome or ("WIN" if return_amount >= 0 else "LOSS")
    trade.learnings = data.learnings
    trade.feedback = data.feedback
    trade.screenshot = data.screenshot
    
    db.commit()
    db.refresh(trade)
    return serialize_trade(trade)

@router.patch("/{trade_id}")
async def update_trade(
    trade_id: int,
    data: TradeUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if data.against_trend is not None:
        trade.against_trend = data.against_trend
    if data.learnings is not None:
        trade.learnings = data.learnings
    if data.feedback is not None:
        trade.feedback = data.feedback
    if data.screenshot is not None:
        trade.screenshot = data.screenshot
    if data.outcome is not None and trade.status == "CLOSED":
        trade.outcome = data.outcome
    if data.exit_price is not None and trade.status == "CLOSED":
        total_qty = sum(e.quantity for e in trade.entries)
        avg_price = trade.avg_price or 0
        trade.exit_price = data.exit_price
        trade.return_amount = (data.exit_price - avg_price) * total_qty
        trade.return_percent = ((data.exit_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
    
    db.commit()
    db.refresh(trade)
    return serialize_trade(trade)

@router.delete("/{trade_id}")
async def delete_trade(
    trade_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trade = db.query(Trade).filter(Trade.id == trade_id, Trade.user_id == user.id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    db.delete(trade)
    db.commit()
    return {"message": "Trade deleted"}

def serialize_trade(trade: Trade) -> dict:
    return {
        "id": trade.id,
        "trade_number": trade.trade_number,
        "symbol": trade.symbol,
        "instrument_type": trade.instrument_type,
        "lot_size": trade.lot_size,
        "avg_price": trade.avg_price,
        "exit_price": trade.exit_price,
        "exit_datetime": trade.exit_datetime.isoformat() if trade.exit_datetime else None,
        "return_percent": trade.return_percent,
        "return_amount": trade.return_amount,
        "status": trade.status,
        "against_trend": trade.against_trend,
        "outcome": trade.outcome,
        "learnings": trade.learnings,
        "feedback": trade.feedback,
        "screenshot": trade.screenshot,
        "created_at": trade.created_at.isoformat(),
        "updated_at": trade.updated_at.isoformat(),
        "entries": [
            {
                "id": e.id,
                "price": e.price,
                "lots": e.lots,
                "quantity": e.quantity,
                "datetime": e.datetime.isoformat()
            }
            for e in trade.entries
        ]
    }
