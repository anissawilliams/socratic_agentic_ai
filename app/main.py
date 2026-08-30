from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.tutor import router as tutor_router


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(tutor_router)