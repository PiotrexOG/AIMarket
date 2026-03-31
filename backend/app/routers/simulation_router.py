from fastapi import APIRouter
from app.dto.simulation_dto import SimulationDetail
from app.services.config_service import ConfigService

router = APIRouter(prefix="/simulation", tags=["Simulations"])

@router.get("/config", response_model=SimulationDetail)
def get_start_end_dates():
    return ConfigService.get_start_end_dates()