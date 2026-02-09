from fastapi import FastAPI

from app.api.routes import router as api_router
from app.api.ui import router as ui_router
from app.config import settings
from app.db import init_db


app = FastAPI(title=settings.app_name)
app.include_router(ui_router)
app.include_router(api_router)


@app.on_event("startup")
def _startup() -> None:
    init_db()
