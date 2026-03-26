from fastapi import APIRouter, HTTPException, status

from ....query_engine import execute_select_query
from ....llm import natural_language_to_sql
from ....schemas.query import QueryRequest, QueryResponse
from ....services.query_service import answer_graph_query
from ....core.config import settings

router = APIRouter()


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Convert ERP natural language to SQL and execute it",
)
async def run_query(request: QueryRequest) -> QueryResponse:
    try:
        if settings.groq_api_key or settings.openai_api_key:
            try:
                sql = natural_language_to_sql(request.question)
                data = execute_select_query(sql)
                graph_result = answer_graph_query(request.question)
                return QueryResponse(
                    answer="Executed a data-backed SQL query for your ERP question.",
                    sql=sql,
                    data=data,
                    graph=graph_result["graph"],
                )
            except Exception:
                pass

        graph_result = answer_graph_query(request.question)
        return QueryResponse(**graph_result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process query.",
        ) from exc
