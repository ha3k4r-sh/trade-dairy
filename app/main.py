from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database import engine, SessionLocal
from app.models.models import Base, User, Settings, PlanTrade, Holiday
from app.auth import get_password_hash, verify_token
from app.config import settings as app_settings
from app.routers import auth, trades, expenses, investments, holidays, settings, dashboard, plan, market
from datetime import datetime

def init_db():
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Create default user if not exists
        user = db.query(User).filter(User.username == app_settings.DEFAULT_USERNAME).first()
        if not user:
            user = User(
                username=app_settings.DEFAULT_USERNAME,
                password_hash=get_password_hash(app_settings.DEFAULT_PASSWORD)
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            
            # Create default settings
            user_settings = Settings(
                user_id=user.id,
                initial_capital=40000,
                target_capital=10000000,
                return_per_trade=4,
                reserve_amount=170000
            )
            db.add(user_settings)
            db.commit()
        
        # Seed plan trades if empty
        if db.query(PlanTrade).count() == 0:
            capital = 40000
            for i in range(1, 201):
                after_close = capital * 1.04
                lots = int(capital / 1000)
                plan_trade = PlanTrade(
                    trade_number=i,
                    initial_investment=capital,
                    profit_percent=4,
                    after_trade_close=after_close,
                    no_of_lots=lots,
                    capital_used=lots * 1000
                )
                db.add(plan_trade)
                capital = after_close
            db.commit()
        
        # Seed holidays if empty
        if db.query(Holiday).count() == 0:
            # 2026 Trading Holidays
            trading_holidays_2026 = [
                ("2026-01-15", "Municipal Corp Election in Maharashtra", "TRADING"),
                ("2026-01-26", "Republic Day", "TRADING"),
                ("2026-03-03", "Holi", "TRADING"),
                ("2026-03-26", "Shri Ram Navami", "TRADING"),
                ("2026-03-31", "Shri Mahavir Jayanti", "TRADING"),
                ("2026-04-03", "Good Friday", "TRADING"),
                ("2026-04-14", "Dr. Baba Saheb Ambedkar Jayanti", "TRADING"),
                ("2026-05-01", "Maharashtra Day", "TRADING"),
                ("2026-05-28", "Bakri Id", "TRADING"),
                ("2026-06-26", "Muharram", "TRADING"),
                ("2026-09-14", "Ganesh Chaturthi", "TRADING"),
                ("2026-10-02", "Mahatma Gandhi Jayanti", "TRADING"),
                ("2026-10-20", "Dussehra", "TRADING"),
                ("2026-11-10", "Diwali-Balipratipada", "TRADING"),
                ("2026-11-24", "Prakash Gurpurb Sri Guru Nanak Dev", "TRADING"),
                ("2026-12-25", "Christmas", "TRADING"),
            ]
            # 2026 Clearing Holidays
            clearing_holidays_2026 = [
                ("2026-01-15", "Municipal Corp Election in Maharashtra", "CLEARING"),
                ("2026-01-26", "Republic Day", "CLEARING"),
                ("2026-02-19", "Chhatrapati Shivaji Maharaj Jayanti", "CLEARING"),
                ("2026-03-03", "Holi (Second Day)", "CLEARING"),
                ("2026-03-19", "Gudhi Padwa", "CLEARING"),
                ("2026-03-26", "Ram Navami", "CLEARING"),
                ("2026-03-31", "Mahavir Jayanti", "CLEARING"),
                ("2026-04-01", "Annual Bank Closing", "CLEARING"),
                ("2026-04-03", "Good Friday", "CLEARING"),
                ("2026-04-14", "Dr. Babasaheb Ambedkar Jayanti", "CLEARING"),
                ("2026-05-01", "Maharashtra Din / Buddha Pournima", "CLEARING"),
                ("2026-05-28", "Bakri ID (Id-Uz-Zuha)", "CLEARING"),
                ("2026-06-26", "Muharram", "CLEARING"),
                ("2026-08-26", "Id-E-Milad", "CLEARING"),
                ("2026-09-14", "Ganesh Chaturthi", "CLEARING"),
                ("2026-10-02", "Mahatma Gandhi Jayanti", "CLEARING"),
                ("2026-10-20", "Dussehra", "CLEARING"),
                ("2026-11-10", "Diwali (Bali Pratipada)", "CLEARING"),
                ("2026-11-24", "Guru Nanak Jayanti", "CLEARING"),
                ("2026-12-25", "Christmas", "CLEARING"),
            ]
            for date_str, desc, htype in trading_holidays_2026 + clearing_holidays_2026:
                h = Holiday(
                    date=datetime.fromisoformat(date_str),
                    description=desc,
                    type=htype
                )
                db.add(h)
            db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Trade Diary", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(auth.router)
app.include_router(trades.router)
app.include_router(expenses.router)
app.include_router(investments.router)
app.include_router(holidays.router)
app.include_router(settings.router)
app.include_router(dashboard.router)
app.include_router(plan.router)
app.include_router(market.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    token = request.cookies.get("access_token")
    if token and verify_token(token):
        return RedirectResponse(url="/app", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/app", response_class=HTMLResponse)
async def app_page(request: Request):
    token = request.cookies.get("access_token")
    if not token or not verify_token(token):
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse("app.html", {"request": request})
