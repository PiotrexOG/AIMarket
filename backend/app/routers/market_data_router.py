from fastapi import APIRouter

router = APIRouter(prefix="/market-data", tags=["MarketData"])

# @router.get("/{ticker}", response_model=List[MarketDataRead])
# def get_recent_data(ticker: str, limit: int = 100, db: Session = Depends(get_db)):
#     service = MarketDataService(db)
#     return service.get_recent_data(ticker, limit)
