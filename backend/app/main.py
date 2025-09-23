# app/main.py
from datetime import timedelta, datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading

from sqlalchemy import desc
from app.db.models.portfolio import PortfolioHistory
from app.simulation.simulation_service import SimulationService
from app.db.database import SessionLocal
from app.config import START_TIME, END_TIME, NO_USERS, STARTING_CASH, TICKERS, DEBUG_RESET, REAL_TIME

app = FastAPI(title="Stock Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerów
from app.routers import users_router, market_data_router, portfolio_router
app.include_router(users_router.router)
app.include_router(market_data_router.router)
app.include_router(portfolio_router.router)


def get_start_datetime(real_time: bool) -> datetime:
    """Określa datę rozpoczęcia symulacji na podstawie flagi i danych w bazie."""
    if real_time:
        now = datetime.now().replace(minute=0, second=0, microsecond=0)
        print(f"🔄 Tryb REAL_TIME: zaczynamy od {now}")
        return now

    with SessionLocal() as session:
        latest_record = (
            session.query(PortfolioHistory)
            .order_by(desc(PortfolioHistory.datetime))
            .first()
        )

        start_time = (
            latest_record.datetime + timedelta(hours=1)
            if latest_record
            else START_TIME
        )

    mode = "Kontynuacja" if latest_record else "Start"
    print(f"{'⏩' if latest_record else '▶'} {mode} od {start_time}")
    return start_time


def run_simulation():
    start_datetime = get_start_datetime(REAL_TIME)

    with SessionLocal() as session:
        simulation_service = SimulationService(
            db=session,
            tickers=TICKERS,
            start_time=start_datetime,
            end_time=END_TIME,
        )

        simulation_service.fetch_market_data(interval="1h")
        simulation_service.initialize_users(
            no_users=NO_USERS,
            starting_cash=STARTING_CASH,
        )
        simulation_service.run_simulation()


# Uruchomienie w tle
threading.Thread(target=run_simulation, daemon=True).start()
uvicorn.run(app, host="0.0.0.0", port=8000)

