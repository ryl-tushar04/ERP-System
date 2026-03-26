from fastapi import APIRouter

from .endpoints.graph import router as graph_router
from .endpoints.health import router as health_router
from .endpoints.query import router as query_router

router = APIRouter()
router.include_router(health_router, tags=["health"])
router.include_router(graph_router, tags=["graph"])
router.include_router(query_router, tags=["query"])
