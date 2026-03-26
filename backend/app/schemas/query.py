from typing import Any

from pydantic import BaseModel, Field, model_validator

from .graph import GraphPayload


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Natural language ERP question")

    @model_validator(mode="before")
    @classmethod
    def normalize_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            question = data.get("question") or data.get("query")
            if question is not None:
                return {"question": question}
        return data


class QueryResponse(BaseModel):
    answer: str
    sql: str | None = None
    data: list[dict[str, Any]]
    graph: GraphPayload | None = None
