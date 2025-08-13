# from pydantic import BaseModel
# from typing import Dict, List
#
# class UserDTO(BaseModel):
#     user_id: int
#     cash: float
#     shares: Dict[str, int]
#     portfolio_value: float
#
#
# class PositionDetail(BaseModel):
#     ticker: str
#     shares: int
#     price: float
#     value: float
#
#
# class UserDetailDTO(BaseModel):
#     user_id: int
#     cash: float
#     portfolio_value: float
#     positions: List[PositionDetail]
#
# class UserDetail2DTO(BaseModel):
#     user_id: int
#     date: str
#     cash: float
#     portfolio_value: float
#     positions: List[PositionDetail]
