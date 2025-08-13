# from typing import List
#
# from fastapi import APIRouter
# from app.services.simulation_service import SimulationService
# from app.models.user_models import UserDTO, UserDetailDTO, UserDetail2DTO
# from fastapi import HTTPException
#
# router = APIRouter()
#
# @router.get("/{user_id}/daily-portfolio/{date}", response_model=UserDetailDTO)
# def get_user_daily_portfolio(user_id: int, date: str):
#     """Get user's portfolio details for a specific date"""
#     user = SimulationService.get_user_daily_portfolio(user_id, date)
#     if not user:
#         raise HTTPException(status_code=404, detail="User portfolio not found for given date")
#     return user
#
# @router.get("/{user_id}/portfolio-history")
# def get_user_portfolio_history(user_id: int):
#     """Get historical portfolio values for a user"""
#     history = SimulationService.get_user_portfolio_history(user_id)
#     if not history:
#         raise HTTPException(status_code=404, detail="User history not found")
#     return history
#
# @router.get("/{user_id}/full-portfolio-history", response_model=List[UserDetail2DTO])
# def get_user_full_portfolio_history(user_id: int):
#     """Get complete historical portfolio details with positions for all dates"""
#     history = SimulationService.get_user_full_portfolio_history(user_id)
#     if not history:
#         raise HTTPException(status_code=404, detail="User portfolio history not found")
#     return history
#
