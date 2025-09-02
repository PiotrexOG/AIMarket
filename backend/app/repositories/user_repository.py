from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, data: UserCreate) -> User:
        if isinstance(data, dict):
            db_obj = User(**data)
        else:
            db_obj = User(**data.dict())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def get(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def get_all(self):
        return self.db.query(User).all()

    def delete_all(self):
        self.db.query(User).delete()
        self.db.commit()
