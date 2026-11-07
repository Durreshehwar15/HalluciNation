import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from .database import Base, database
from .routes.tickets import router
from .services.docker_runner import DockerRunner
from .services.github_service import GitHubService, IntegrationError
from .services.switch_adapter import MockSwitchAdapter


def create_app(
    database_url=None,
    human_token=None,
    human_identity=None,
    github=None,
    runner=None,
    switch=None,
):
    engine, sessions = database(
        database_url or os.getenv("DATABASE_URL", "sqlite:///./tickets.db")
    )
    Base.metadata.create_all(engine)

    @asynccontextmanager
    async def lifespan(app):
        yield
        engine.dispose()

    app = FastAPI(
        title="Support Ticket to Merged Fix", version="0.1.0", lifespan=lifespan
    )
    app.state.sessions = sessions
    app.state.human_token = (
        human_token
        if human_token is not None
        else os.getenv("HUMAN_APPROVAL_TOKEN", "")
    )
    app.state.human_identity = human_identity or os.getenv(
        "HUMAN_APPROVER_ID", "human-reviewer"
    )
    app.state.github = github or GitHubService(os.getenv("GITHUB_TOKEN", ""))
    app.state.runner = runner or DockerRunner(
        app.state.github,
        os.getenv("VERIFIER_IMAGE", "support-fix-verifier:local"),
        project_dir=os.getenv("VERIFIER_PROJECT_DIR", ""),
    )
    app.state.switch = switch or MockSwitchAdapter(
        os.getenv("MOCK_PATCH_PATH", "app.py")
    )
    origins = [
        o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type"],
    )
    from fastapi import HTTPException

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": str(exc.status_code), "message": exc.detail}},
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Request does not match the API contract",
                    "details": [
                        {"location": list(e["loc"]), "message": e["msg"]}
                        for e in exc.errors()
                    ],
                }
            },
        )

    @app.exception_handler(IntegrationError)
    async def integration_error(request, exc):
        return JSONResponse(
            status_code=502,
            content={"error": {"code": "integration_error", "message": str(exc)}},
        )

    @app.exception_handler(OperationalError)
    async def database_busy(request, exc):
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "database_unavailable",
                    "message": "Database unavailable; retry shortly",
                }
            },
            headers={"Retry-After": "1"},
        )

    app.include_router(router)
    return app


app = create_app()
