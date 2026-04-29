# app/main.py
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading

from sqlalchemy import desc
from app.db.models.portfolio import PortfolioHistory
from app.simulation.simulation_service import SimulationService
from app.db.database import SessionLocal
from app.config.config import ZERO_TIME, START_TIME, END_TIME, TICKERS, TIMEDELTA

app = FastAPI(title="Stock Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerów
from app.routers import users_router, market_data_router, portfolio_router, simulation_router, archetype_router
app.include_router(users_router.router)
app.include_router(market_data_router.router)
app.include_router(portfolio_router.router)
app.include_router(simulation_router.router)
app.include_router(archetype_router.router)


def get_start_datetime() -> datetime:

    with SessionLocal() as session:
        latest_record = (
            session.query(PortfolioHistory)
            .order_by(desc(PortfolioHistory.datetime))
            .first()
        )

        start_time = (
            latest_record.datetime + TIMEDELTA
            if latest_record
            else START_TIME
        )

    mode = "Kontynuacja" if latest_record else "Start"
    print(f"{'⏩' if latest_record else '▶'} {mode} od {start_time}")
    return start_time


def run_simulation():
    start_datetime = get_start_datetime()

    with SessionLocal() as session:
        simulation_service = SimulationService(
            db=session,
            tickers=TICKERS,
            zero_time=ZERO_TIME,
            start_time=start_datetime,
            end_time=END_TIME,
        )

        simulation_service.run_simulation()


# Uruchomienie w tle
threading.Thread(target=run_simulation, daemon=True).start()
uvicorn.run(app, host="0.0.0.0", port=8000)

