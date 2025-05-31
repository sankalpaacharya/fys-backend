from fastapi import FastAPI
from app.routes import route
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.config.settings import settings

app = FastAPI(title="FYS Backend")

app.include_router(route.router)

app.add_middleware(SessionMiddleware, secret_key=settings.FAST_API_KEY)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"AI": "Hello Humans!"}