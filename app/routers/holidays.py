from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.models import User, Holiday
from app.auth import get_current_user

router = APIRouter(prefix="/api/holidays", tags=["holidays"])

class HolidayCreate(BaseModel):
    date: str
    description: str
    type: str = "TRADING"

@router.get("")
async def get_holidays(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    holidays = db.query(Holiday).order_by(Holiday.date.asc()).all()
    return [
        {
            "id": h.id,
            "date": h.date.isoformat(),
            "description": h.description,
            "type": h.type
        }
        for h in holidays
    ]

@router.post("")
async def create_holiday(
    data: HolidayCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    holiday = Holiday(
        date=datetime.fromisoformat(data.date),
        description=data.description,
        type=data.type
    )
    db.add(holiday)
    db.commit()
    db.refresh(holiday)
    return {
        "id": holiday.id,
        "date": holiday.date.isoformat(),
        "description": holiday.description,
        "type": holiday.type
    }

@router.delete("/{holiday_id}")
async def delete_holiday(
    holiday_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    holiday = db.query(Holiday).filter(Holiday.id == holiday_id).first()
    if not holiday:
        raise HTTPException(status_code=404, detail="Holiday not found")
    
    db.delete(holiday)
    db.commit()
    return {"message": "Holiday deleted"}
