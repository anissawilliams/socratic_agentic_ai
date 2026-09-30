from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.tutor import router as tutor_router
from app.api.auth.routes import router as auth_router
from app.api.assessments import router as assessments_router
from app.api.study_forms import router as study_forms_router
from contextlib import asynccontextmanager

import anyio


@asynccontextmanager
async def lifespan(app):
    anyio.to_thread.current_default_thread_limiter().total_tokens = 100
    yield


app = FastAPI(lifespan=lifespan)


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
app.include_router(assessments_router)
app.include_router(study_forms_router)