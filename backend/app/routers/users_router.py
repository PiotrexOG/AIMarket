from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.schemas.user import UserRead
from app.services.user_service import UserService
from app.db.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    service = UserService(db)
    user = service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/", response_model=List[UserRead])
def list_users(db: Session = Depends(get_db)):
    service = UserService(db)
    return service.list_users()
