import threading
from datetime import timedelta
from threading import Lock
from typing import List

from fastapi import APIRouter, HTTPException, Path

from app.dto.archetype_dto import ArchetypeRead
from app.dto.simulation_dto import SimulationDetail, SimulationRequest
from app.services.archetype_service import ArchetypeService
from app.services.config_service import ConfigService
from app.simulation.simulation_runner import run_simulation, get_start_datetime, run_simulation_batch
from app.db.database import reset_database

router = APIRouter(prefix="/simulation", tags=["Simulations"])

# 🔐 Global state + lock
simulation_running = False
reset_running = False
lock = Lock()


@router.get("/archetypes/", response_model=List[ArchetypeRead])
def list_all_archetypes():
    """Pobiera listę wszystkich dostępnych strategii (archetypów) botów."""
    archetype_config = ConfigService.get_archetype_config()
    return ArchetypeService(archetype_config=archetype_config.archetypes_config).get_all_archetypes()

@router.get("/archetypes/{archetype_key}", response_model=ArchetypeRead)
def get_archetype_details(
    archetype_key: str = Path(..., description="Klucz archetypu, np. 'degen_trader'")

):
    """Pobiera szczegółową konfigurację konkretnego archetypu."""
    archetype_config = ConfigService.get_archetype_config()
    archetype = ArchetypeService(archetype_config=archetype_config.archetypes_config).get_archetype_by_key(archetype_key)
    if not archetype:
        raise HTTPException(status_code=404, detail="Archetype not found")
    return archetype


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

            ConfigService.set_archetype_config(req.archetypes_config)

            if req.is_batch:
                run_simulation_batch(
                    start_time,
                    req.end_time,
                    req.users_per_archetype,
                    delta,
                    req.archetypes_config
                )
            else:
                run_simulation(
                    start_time,
                    req.end_time,
                    req.users_per_archetype,
                    delta,
                    req.archetypes_config
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