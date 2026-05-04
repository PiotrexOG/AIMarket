import threading
from datetime import timedelta
from threading import Lock

from fastapi import APIRouter, HTTPException

from app.dto.simulation_dto import SimulationDetail, SimulationRequest
from app.services.config_service import ConfigService
from app.simulation.simulation_runner import run_simulation, get_start_datetime
from app.db.database import reset_database

router = APIRouter(prefix="/simulation", tags=["Simulations"])

# 🔐 Global state + lock
simulation_running = False
reset_running = False
lock = Lock()


# 📊 GET CONFIG
@router.get("/config", response_model=SimulationDetail)
def get_start_end_dates():
    return ConfigService.get_start_end_dates()


# ▶️ START SIMULATION
@router.post("/start")
def start_simulation(req: SimulationRequest):
    global simulation_running, reset_running

    with lock:
        if simulation_running or reset_running:
            return {"status": "busy"}

        simulation_running = True

    def wrapper():
        global simulation_running
        try:
            delta = timedelta(days=req.delta_days)

            start_time = get_start_datetime(req.start_time, delta)

            ConfigService.set_start_end_dates(
                start_time,
                req.end_time
            )

            run_simulation(
                start_time,
                req.end_time,
                req.users_per_archetype,
                delta,
            )
        except Exception as e:
            print(f"[SIMULATION ERROR] {e}")
        finally:
            simulation_running = False

    threading.Thread(target=wrapper, daemon=True).start()

    return {"status": "simulation started"}


# 🔄 RESET DATABASE
@router.post("/reset")
def reset_db():
    global simulation_running, reset_running

    with lock:
        if simulation_running or reset_running:
            return {"status": "busy"}

        reset_running = True

    def wrapper():
        global reset_running
        try:
            reset_database()
        except Exception as e:
            print(f"[RESET ERROR] {e}")
        finally:
            reset_running = False

    threading.Thread(target=wrapper, daemon=True).start()

    return {"status": "reset started"}