# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
from app.services.simulation_service_new import SimulationService
from app.database import SessionLocal
from app.config import START_TIME, END_TIME, NO_USERS, STARTING_CASH, TICKERS

app = FastAPI(title="Stock Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerów
from app.routers import users_router, market_data_router
app.include_router(users_router.router)
app.include_router(market_data_router.router)

# -------------------------------
# Funkcja uruchamiająca symulację
# -------------------------------
def run_simulation():
    print("✅ Symulacja zakończona.")
    db = SessionLocal()
    try:
        simulation_service = SimulationService(
            db=db,
            tickers=TICKERS,
            start_time=START_TIME,
            end_time=END_TIME
        )
        simulation_service.fetch_market_data(interval="1h")
        simulation_service.initialize_users(no_users=NO_USERS, starting_cash=STARTING_CASH)
        simulation_service.run_simulation()
    finally:
        db.close()

# Uruchamiamy w tle przy starcie serwera
threading.Thread(target=run_simulation, daemon=True).start()
