from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import init_db
from .routes import router

settings = get_settings()
app = FastAPI(title=settings.app_name, version="1.0.0", description="AI-powered 7-day fitness plan generator")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


@app.on_event("startup")
def startup() -> None:
    init_db()
