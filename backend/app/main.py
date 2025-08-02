from fastapi import FastAPI
from app.api import users
from app.services.simulation_service import SimulationService

# FastAPI:
from fastapi.middleware.cors import CORSMiddleware



app = FastAPI(title="Stock Simulator API")

SimulationService.initialize_users()

app.include_router(users.router, prefix="/users", tags=["Users"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
