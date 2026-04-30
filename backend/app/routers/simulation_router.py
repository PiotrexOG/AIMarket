import threading
from datetime import timedelta

from cffi.cparser import lock
from fastapi import APIRouter

from app.dto.simulation_dto import SimulationDetail, SimulationRequest
from app.services.config_service import ConfigService
from app.simulation.simulation_runner import run_simulation, get_start_datetime

router = APIRouter(prefix="/simulation", tags=["Simulations"])

@router.get("/config", response_model=SimulationDetail)
def get_start_end_dates():
    return ConfigService.get_start_end_dates()


simulation_running = False
@router.post("/simulation/start")
def start_simulation(req: SimulationRequest):
    global simulation_running

    with lock:
        if simulation_running:
            return {"status": "already running"}

        simulation_running = True

    def wrapper():
        global simulation_running
        try:
            delta = timedelta(days=req.delta_days)

            start_time = get_start_datetime(req.start_time, delta)
            ConfigService.set_start_end_dates(start_time, req.end_time)

            run_simulation(
                start_time,
                req.end_time,
                req.users_per_archetype,
                delta,
            )
        finally:
            simulation_running = False

    threading.Thread(target=wrapper, daemon=True).start()

    return {"status": "started"}