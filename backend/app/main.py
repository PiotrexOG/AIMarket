# app/main.py

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Stock Simulator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rejestracja routerów
from app.routers import users_router, market_data_router, portfolio_router, simulation_router
app.include_router(users_router.router)
app.include_router(market_data_router.router)
app.include_router(portfolio_router.router)
app.include_router(simulation_router.router)

# Uruchomienie w tle
uvicorn.run(app, host="0.0.0.0", port=8000)

