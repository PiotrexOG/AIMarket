from fastapi import FastAPI
from app.api import users
from app.config import STARTING_CASH, NO_USERS
from app.services.simulation_service import SimulationService

# FastAPI:
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="Stock Simulator API")

SimulationService.initialize_users(NO_USERS, STARTING_CASH)

SimulationService.start_simulation()

app.include_router(users.router, prefix="/users", tags=["Users"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
