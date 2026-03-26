from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.router import api_router
from .core.config import settings
from .query_engine import close_connection_pool


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        close_connection_pool()


def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="ERP query API for converting natural language into SQL and executing read-only reports.",
        lifespan=lifespan,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            {
                "message": "ERP Workflow Debugging System API is running.",
                "docs": "/docs",
                "health": f"{settings.api_v1_prefix}/health",
                "query": f"{settings.api_v1_prefix}/query",
                "graph": f"{settings.api_v1_prefix}/graph",
            }
        )

    app.include_router(api_router, prefix=settings.api_v1_prefix)
    return app


app = create_application()
