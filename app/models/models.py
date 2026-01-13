from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    totp_secret = Column(String(32), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    settings = relationship("Settings", back_populates="user", uselist=False)
    trades = relationship("Trade", back_populates="user")
    expenses = relationship("Expense", back_populates="user")
    investments = relationship("Investment", back_populates="user")
    withdrawals = relationship("Withdrawal", back_populates="user")

class Settings(Base):
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    initial_capital = Column(Float, default=40000)
    target_capital = Column(Float, default=10000000)
    return_per_trade = Column(Float, default=4)
    reserve_amount = Column(Float, default=170000)
    nifty_lot_size = Column(Integer, default=65)
    banknifty_lot_size = Column(Integer, default=30)
    finnifty_lot_size = Column(Integer, default=60)
    nifty_expiry_day = Column(String(20), default="TUESDAY")
    
    user = relationship("User", back_populates="settings")

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    trade_number = Column(Integer)
    symbol = Column(String(50))
    instrument_type = Column(String(50))
    lot_size = Column(Integer)
    avg_price = Column(Float, nullable=True)
    exit_price = Column(Float, nullable=True)
    exit_datetime = Column(DateTime, nullable=True)
    return_percent = Column(Float, nullable=True)
    return_amount = Column(Float, nullable=True)
    status = Column(String(20), default="OPEN")
    against_trend = Column(Boolean, default=False)
    outcome = Column(String(20), nullable=True)
    learnings = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)
    screenshot = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="trades")
    entries = relationship("TradeEntry", back_populates="trade", cascade="all, delete-orphan")

class TradeEntry(Base):
    __tablename__ = "trade_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"))
    price = Column(Float)
    lots = Column(Integer)
    quantity = Column(Integer)
    datetime = Column(DateTime, default=datetime.utcnow)
    
    trade = relationship("Trade", back_populates="entries")

class Expense(Base):
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    category = Column(String(50))
    name = Column(String(100))
    amount = Column(Float)
    billing_cycle = Column(String(20))
    next_due_date = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="expenses")
    payments = relationship("ExpensePayment", back_populates="expense", cascade="all, delete-orphan")

class ExpensePayment(Base):
    __tablename__ = "expense_payments"
    
    id = Column(Integer, primary_key=True, index=True)
    expense_id = Column(Integer, ForeignKey("expenses.id"))
    amount_paid = Column(Float)
    payment_date = Column(DateTime)
    payment_method = Column(String(50), nullable=True)
    
    expense = relationship("Expense", back_populates="payments")

class Investment(Base):
    __tablename__ = "investments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(50))
    amount = Column(Float)
    source = Column(String(50))
    date = Column(DateTime)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="investments")

class Withdrawal(Base):
    __tablename__ = "withdrawals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    amount = Column(Float)
    reason = Column(Text, nullable=True)
    date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="withdrawals")

class Holiday(Base):
    __tablename__ = "holidays"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime)
    description = Column(String(200))
    type = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)

class PlanTrade(Base):
    __tablename__ = "plan_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_number = Column(Integer, unique=True)
    initial_investment = Column(Float)
    profit_percent = Column(Float)
    after_trade_close = Column(Float)
    no_of_lots = Column(Integer)
    capital_used = Column(Float)
