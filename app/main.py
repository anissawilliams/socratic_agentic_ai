from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tutor import router as tutor_router

app = FastAPI(title="Socratic Tutor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5175"],  # Vite's default dev port
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tutor_router)