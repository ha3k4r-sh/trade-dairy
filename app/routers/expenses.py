from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import User, Expense, ExpensePayment
from app.auth import get_current_user

router = APIRouter(prefix="/api/expenses", tags=["expenses"])

class ExpenseCreate(BaseModel):
    category: str
    name: str
    amount: float
    billing_cycle: str
    next_due_date: Optional[str] = None
    auto_renew: bool = True
    notes: Optional[str] = None

class ExpenseUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None
    is_active: Optional[bool] = None
    amount: Optional[float] = None
    billing_cycle: Optional[str] = None
    next_due_date: Optional[str] = None
    auto_renew: Optional[bool] = None
    notes: Optional[str] = None

@router.get("")
async def get_expenses(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expenses = db.query(Expense).filter(Expense.user_id == user.id).order_by(Expense.created_at.desc()).all()
    return [serialize_expense(e) for e in expenses]

@router.get("/{expense_id}")
async def get_expense(
    expense_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    return serialize_expense(expense)

@router.post("")
async def create_expense(
    data: ExpenseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = Expense(
        user_id=user.id,
        category=data.category,
        name=data.name,
        amount=data.amount,
        billing_cycle=data.billing_cycle,
        next_due_date=datetime.fromisoformat(data.next_due_date) if data.next_due_date else None,
        auto_renew=data.auto_renew,
        notes=data.notes
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return serialize_expense(expense)

@router.patch("/{expense_id}")
async def update_expense(
    expense_id: int,
    data: ExpenseUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    if data.category is not None:
        expense.category = data.category
    if data.name is not None:
        expense.name = data.name
    if data.is_active is not None:
        expense.is_active = data.is_active
    if data.amount is not None:
        expense.amount = data.amount
    if data.billing_cycle is not None:
        expense.billing_cycle = data.billing_cycle
    if data.next_due_date is not None:
        expense.next_due_date = datetime.fromisoformat(data.next_due_date) if data.next_due_date else None
    if data.auto_renew is not None:
        expense.auto_renew = data.auto_renew
    if data.notes is not None:
        expense.notes = data.notes
    
    db.commit()
    db.refresh(expense)
    return serialize_expense(expense)

@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted"}

@router.post("/{expense_id}/payment")
async def record_payment(
    expense_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    payment = ExpensePayment(
        expense_id=expense.id,
        amount_paid=expense.amount,
        payment_date=datetime.utcnow()
    )
    db.add(payment)
    
    # Update next due date if auto-renew
    if expense.auto_renew and expense.next_due_date:
        if expense.billing_cycle == "MONTHLY":
            expense.next_due_date = expense.next_due_date + timedelta(days=30)
        elif expense.billing_cycle == "YEARLY":
            expense.next_due_date = expense.next_due_date + timedelta(days=365)
    
    db.commit()
    return {"message": "Payment recorded"}

def serialize_expense(expense: Expense) -> dict:
    return {
        "id": expense.id,
        "category": expense.category,
        "name": expense.name,
        "amount": expense.amount,
        "billing_cycle": expense.billing_cycle,
        "next_due_date": expense.next_due_date.isoformat() if expense.next_due_date else None,
        "auto_renew": expense.auto_renew,
        "notes": expense.notes,
        "is_active": expense.is_active,
        "created_at": expense.created_at.isoformat(),
        "payments": [
            {
                "id": p.id,
                "amount_paid": p.amount_paid,
                "payment_date": p.payment_date.isoformat()
            }
            for p in expense.payments
        ]
    }
