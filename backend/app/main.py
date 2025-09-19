# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading

from sqlalchemy import desc

from app.db.models.market_data import MarketData
from app.db.models.portfolio import PortfolioHistory
from app.db.models.portfolio import Portfolio
from app.db.models.user import User
from app.simulation.simulation_service import SimulationService
from app.db.database import SessionLocal
from app.config import START_TIME, END_TIME, NO_USERS, STARTING_CASH, TICKERS, DEBUG_RESET

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

# -------------------------------
# Funkcja uruchamiająca symulację
# -------------------------------
def run_simulation():
    db = SessionLocal()
    try:

        with SessionLocal() as session:
            market_data_exists = session.query(MarketData).first() is not None
            portfolios = session.query(Portfolio).first() is not None
            users = session.query(User).first() is not None
            latest_record = session.query(PortfolioHistory) \
                .order_by(desc(PortfolioHistory.datetime)) \
                .first()

            if latest_record:
                latest_datetime = latest_record.datetime
                print("Zaczynamy od daty bo juz cos bylo " + str(latest_datetime))
            else:
                latest_datetime = START_TIME
                print("Zaczynamy od daty poczatkowej " + str(latest_datetime))

        simulation_service = SimulationService(
            db=db,
            tickers=TICKERS,
            start_time=latest_datetime,
            end_time=END_TIME
        )

        if not market_data_exists:
            simulation_service.fetch_market_data(interval="1h")
        else:
            print("Dane rynkowe już istnieją, pomijam pobieranie")

        if not users or not portfolios:
            print("zrobilem uizytkownikow i portoflio")
            simulation_service.initialize_users(no_users=NO_USERS, starting_cash=STARTING_CASH)

        simulation_service.run_simulation()
    finally:
        db.close()

# Uruchamiamy w tle przy starcie serwera
threading.Thread(target=run_simulation, daemon=True).start()
uvicorn.run(app, host="0.0.0.0", port=8000)
