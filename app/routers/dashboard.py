from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.database import get_db
from app.models.models import User, Trade, Expense, Investment, Withdrawal, Holiday, Settings, PlanTrade
from app.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("")
async def get_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Settings
    settings = db.query(Settings).filter(Settings.user_id == user.id).first()
    if not settings:
        settings = Settings(
            user_id=user.id,
            initial_capital=40000,
            target_capital=10000000,
            return_per_trade=4,
            reserve_amount=170000
        )
        db.add(settings)
        db.commit()
    
    # Trades
    trades = db.query(Trade).filter(Trade.user_id == user.id).all()
    open_trades = [t for t in trades if t.status == "OPEN"]
    closed_trades = [t for t in trades if t.status == "CLOSED"]
    
    total_pl = sum(t.return_amount or 0 for t in closed_trades)
    winning_trades = [t for t in closed_trades if (t.return_amount or 0) > 0]
    win_rate = (len(winning_trades) / len(closed_trades) * 100) if closed_trades else 0
    
    # Weekly trades
    week_start = datetime.utcnow() - timedelta(days=7)
    weekly_trades = [t for t in closed_trades if t.updated_at >= week_start]
    weekly_pl = sum(t.return_amount or 0 for t in weekly_trades)
    
    # Investments & Withdrawals
    investments = db.query(Investment).filter(Investment.user_id == user.id).all()
    withdrawals = db.query(Withdrawal).filter(Withdrawal.user_id == user.id).all()
    total_invested = sum(i.amount for i in investments)
    total_withdrawn = sum(w.amount for w in withdrawals)
    current_capital = total_invested + total_pl - total_withdrawn
    
    # Expenses
    expenses = db.query(Expense).filter(Expense.user_id == user.id, Expense.is_active == True).all()
    monthly_expenses = sum(e.amount for e in expenses if e.billing_cycle == "MONTHLY")
    
    # Upcoming holidays
    now = datetime.utcnow()
    upcoming_holidays = db.query(Holiday).filter(
        Holiday.date >= now,
        Holiday.date <= now + timedelta(days=7)
    ).order_by(Holiday.date.asc()).limit(3).all()
    
    # Next plan trade
    next_trade_number = len(trades) + 1
    next_plan_trade = db.query(PlanTrade).filter(PlanTrade.trade_number == next_trade_number).first()
    
    # Goal progress
    goal_progress = ((current_capital - settings.initial_capital) / 
                     (settings.target_capital - settings.initial_capital) * 100) if settings.target_capital > settings.initial_capital else 0
    
    return {
        "current_capital": current_capital,
        "total_invested": total_invested,
        "total_withdrawn": total_withdrawn,
        "total_pl": total_pl,
        "weekly_pl": weekly_pl,
        "weekly_trades_count": len(weekly_trades),
        "win_rate": win_rate,
        "winning_trades": len(winning_trades),
        "total_closed_trades": len(closed_trades),
        "open_trades_count": len(open_trades),
        "monthly_expenses": monthly_expenses,
        "active_subscriptions": len(expenses),
        "goal_progress": goal_progress,
        "trades_completed": len(closed_trades),
        "trades_remaining": 200 - len(closed_trades),
        "upcoming_holidays": [
            {
                "id": h.id,
                "date": h.date.isoformat(),
                "description": h.description,
                "days_until": (h.date - now).days
            }
            for h in upcoming_holidays
        ],
        "open_trades": [
            {
                "id": t.id,
                "trade_number": t.trade_number,
                "symbol": t.symbol,
                "avg_price": t.avg_price
            }
            for t in open_trades[:5]
        ],
        "recent_trades": [
            {
                "id": t.id,
                "trade_number": t.trade_number,
                "symbol": t.symbol,
                "return_amount": t.return_amount,
                "updated_at": t.updated_at.isoformat()
            }
            for t in sorted(closed_trades, key=lambda x: x.updated_at, reverse=True)[:5]
        ],
        "next_plan_trade": {
            "trade_number": next_plan_trade.trade_number,
            "initial_investment": next_plan_trade.initial_investment,
            "after_trade_close": next_plan_trade.after_trade_close,
            "is_ahead": current_capital >= next_plan_trade.initial_investment
        } if next_plan_trade else None,
        "settings": {
            "initial_capital": settings.initial_capital,
            "target_capital": settings.target_capital,
            "return_per_trade": settings.return_per_trade,
            "reserve_amount": settings.reserve_amount
        }
    }

@router.get("/weekly-chart")
async def get_weekly_chart(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trades = db.query(Trade).filter(
        Trade.user_id == user.id,
        Trade.status == "CLOSED"
    ).all()
    
    # Last 7 days
    result = []
    for i in range(6, -1, -1):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_trades = [t for t in trades if day_start <= t.updated_at < day_end]
        day_pl = sum(t.return_amount or 0 for t in day_trades)
        
        result.append({
            "date": day_start.strftime("%a"),
            "amount": day_pl
        })
    
    return result
