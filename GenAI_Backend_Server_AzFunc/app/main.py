from fastapi import FastAPI
from app.api.v1.router import api_router
from app.core.logging import setup_logging

def create_app() -> FastAPI:
    setup_logging()

    app = FastAPI(
        title="Bug Management Analysis API",
        version="1.0.0"
    )

    app.include_router(api_router, prefix="/api/v1")
    return app

app = create_app()
