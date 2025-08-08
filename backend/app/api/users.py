from fastapi import APIRouter
from app.services.simulation_service import SimulationService
from app.models.user_models import UserDTO, UserDetailDTO
from fastapi import HTTPException

router = APIRouter()

@router.get("/", response_model=list[UserDTO])


@router.get("/{user_id}/{day_str}", response_model=UserDetailDTO)
def get_user(user_id: int, day_str: str):
    user = SimulationService.get_user(user_id, day_str)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
