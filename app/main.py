from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.tutor import router as tutor_router
from app.api.auth.routes import router as auth_router

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
       "http://localhost:5173",
       "https://socraticai-production.up.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(tutor_router)
app.include_router(auth_router)