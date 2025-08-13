from sqlalchemy.orm import Session
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate

class UserService:
    def __init__(self, db: Session):
        self.repo = UserRepository(db)

    def create_user(self, data: UserCreate):
        """
        Tworzy nowego użytkownika.
        """
        return self.repo.create(data)

    def get_user(self, user_id: int):
        """
        Pobiera użytkownika po ID.
        """
        return self.repo.get(user_id)

    def list_users(self):
        """
        Pobiera listę wszystkich użytkowników.
        """
        return self.repo.get_all()
