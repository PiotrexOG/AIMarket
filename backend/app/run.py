# import threading
# from sqlalchemy.orm import Session
# from app.database import SessionLocal
# from app.config import START_TIME, END_TIME, NO_USERS, STARTING_CASH, TICKERS
# from app.services.simulation_service_new import SimulationService
# from app.main import app
# import uvicorn
#
#
# def run_simulation():
#     db: Session = SessionLocal()
#     try:
#         print("✅ Starting simulation")
#
#         simulation_service = SimulationService(
#             db=db,
#             tickers=TICKERS,
#             start_time=START_TIME,
#             end_time=END_TIME
#         )
#
#         print("✅ Fetching market data")
#         simulation_service.fetch_market_data(interval="1h")
#
#         print("✅ Initializing users")
#         simulation_service.initialize_users(no_users=NO_USERS, starting_cash=STARTING_CASH)
#
#         print("✅ Running simulation")
#         simulation_service.run_simulation()
#     finally:
#         db.close()
#
#
# if __name__ == "__main__":
#     # Uruchom symulację w tle
#     threading.Thread(target=run_simulation, daemon=True).start()
#
#     # Uruchom serwer
#     uvicorn.run(app, host="0.0.0.0", port=8000)