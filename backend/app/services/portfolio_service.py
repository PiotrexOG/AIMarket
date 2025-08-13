from sqlalchemy.orm import Session
from app.repositories.portfolio_repository import PortfolioRepository
from app.schemas.portfolio import PortfolioCreate, PortfolioHistoryCreate

class PortfolioService:
    def __init__(self, db: Session):
        self.repo = PortfolioRepository(db)

    # ---- Portfele ----
    def create_portfolio(self, data: PortfolioCreate):
        """
        Tworzy nowy portfel dla użytkownika.
        """
        return self.repo.create_portfolio(data)

    def get_portfolio(self, portfolio_id: int):
        """
        Pobiera szczegóły portfela.
        """
        return self.repo.get_portfolio(portfolio_id)

    def get_user_portfolios(self, user_id: int):
        """
        Pobiera wszystkie portfele danego użytkownika.
        """
        return self.repo.get_user_portfolios(user_id)

    # ---- Historia ----
    def add_portfolio_history(self, portfolio_id: int, history_data: PortfolioHistoryCreate):
        """
        Dodaje wpis historii do portfela wraz z akcjami.
        """
        return self.repo.add_history(portfolio_id, history_data)
