# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import threading
from app.services.simulation_service_new import SimulationService
from app.database import SessionLocal
from app.config import START_TIME, END_TIME, NO_USERS, STARTING_CASH, TICKERS, FIRST_RUN, DEBUG_RESET

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
        simulation_service = SimulationService(
            db=db,
            tickers=TICKERS,
            start_time=START_TIME,
            end_time=END_TIME
        )

        if DEBUG_RESET:
            print("⚠️ RESET_DB=True → czyszczę wszystkie tabele...")

            if FIRST_RUN:
                simulation_service.market_data_service.delete_all()
                simulation_service.fetch_market_data(interval="1h")



            simulation_service.portfolio_service.delete_all()
            simulation_service.user_service.delete_all()

            simulation_service.initialize_users(no_users=NO_USERS, starting_cash=STARTING_CASH)

        simulation_service.run_simulation()
    finally:
        db.close()

# Uruchamiamy w tle przy starcie serwera
threading.Thread(target=run_simulation, daemon=True).start()
uvicorn.run(app, host="0.0.0.0", port=8000)
