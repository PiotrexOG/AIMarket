# app/services/simulation_runner.py

from sqlalchemy import desc
from app.db.models.portfolio import PortfolioHistory
from app.simulation.simulation_service import SimulationService
from app.db.database import SessionLocal
from app.config.config import ZERO_TIME, TICKERS


def get_start_datetime(default_start, delta_days):
    with SessionLocal() as session:
        latest_record = (
            session.query(PortfolioHistory)
            .order_by(desc(PortfolioHistory.datetime))
            .first()
        )

        start_time = (
            latest_record.datetime + delta_days
            if latest_record
            else default_start
        )

    return start_time


def run_simulation(start_datetime, end_time, users_per_archetype, delta_days):
    with SessionLocal() as session:
        simulation_service = SimulationService(
            db=session,
            tickers=TICKERS,
            zero_time=ZERO_TIME,
            start_time=start_datetime,
            end_time=end_time,
            users_per_archetype=users_per_archetype,
            delta_days=delta_days
        )

        simulation_service.run_simulation()