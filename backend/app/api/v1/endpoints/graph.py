from fastapi import APIRouter, HTTPException, Query, status

from ....services.graph_store import get_graph_store, get_overview_graph_store

router = APIRouter()


@router.get("/graph", summary="Get the full ERP graph")
async def get_graph():
    return get_overview_graph_store().get_graph()


@router.get("/graph/search", summary="Search graph nodes")
async def search_graph(q: str = Query("", description="Free-text graph search")):
    return {"results": get_graph_store().search_nodes(q)}


@router.get("/graph/nodes/{node_id}", summary="Get node detail and neighbors")
async def get_graph_node(node_id: str):
    store = get_graph_store()
    try:
        return store.get_node_detail(node_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Node '{node_id}' was not found in the graph.",
        ) from exc
