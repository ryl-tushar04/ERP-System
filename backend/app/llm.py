import json
import re
from typing import Iterable

from openai import OpenAI
from pydantic import BaseModel

from .core.config import settings
from .services.ai.client import get_openai_client
from .services.ai.guardrails import validate_erp_query


class SQLOnlyResponse(BaseModel):
    sql: str


_ALLOWED_TABLES = {"orders", "deliveries", "invoices", "payments"}
_FORBIDDEN_SQL = re.compile(
    r"\b(insert|update|delete|drop|alter|truncate|create|grant|revoke)\b",
    re.IGNORECASE,
)
_TABLE_REF = re.compile(r"\b(?:from|join)\s+([a-z_][a-z0-9_]*)\b", re.IGNORECASE)
_SQL_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "sql_only_response",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "sql": {"type": "string"},
            },
            "required": ["sql"],
            "additionalProperties": False,
        },
    },
}


def _extract_tables(sql: str) -> set[str]:
    return {match.lower() for match in _TABLE_REF.findall(sql)}


def _validate_sql(sql: str, allowed_tables: Iterable[str]) -> str:
    cleaned = sql.strip().rstrip(";")
    if not cleaned:
        raise ValueError("Model returned empty SQL.")

    if _FORBIDDEN_SQL.search(cleaned):
        raise ValueError("Only read-only SQL is allowed.")

    if not re.match(r"^(select|with)\b", cleaned, flags=re.IGNORECASE):
        raise ValueError("Only SELECT queries are allowed.")

    referenced_tables = _extract_tables(cleaned)
    unknown_tables = referenced_tables - {table.lower() for table in allowed_tables}
    if unknown_tables:
        raise ValueError(f"SQL referenced unknown tables: {sorted(unknown_tables)}")

    return cleaned + ";"


def natural_language_to_sql(
    question: str,
    client: OpenAI | None = None,
    model: str | None = None,
) -> str:
    question = validate_erp_query(question)

    client = client or get_openai_client()
    model = model or settings.openai_model

    schema_description = """
Available tables and join path:
- orders(order_id, customer_id, order_number, order_date, status, total_amount)
- deliveries(delivery_id, order_id, delivery_number, delivery_date, status)
- invoices(invoice_id, delivery_id, invoice_number, invoice_date, status, invoice_amount, due_date)
- payments(payment_id, invoice_id, payment_reference, payment_date, payment_method, amount_paid, status)

Join rules:
- deliveries.order_id = orders.order_id
- invoices.delivery_id = deliveries.delivery_id
- payments.invoice_id = invoices.invoice_id

Requirements:
- Output exactly one PostgreSQL SELECT query
- Use only the tables and columns listed above
- Use joins only through the join rules above
- Do not invent tables, columns, or relationships
- If the request is ambiguous, return the safest valid SELECT using available fields only
""".strip()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": schema_description},
            {"role": "user", "content": question},
        ],
        response_format=_SQL_RESPONSE_SCHEMA,
    )

    content = response.choices[0].message.content or "{}"
    sql = SQLOnlyResponse(**json.loads(content)).sql
    return _validate_sql(sql, _ALLOWED_TABLES)


__all__ = ["get_openai_client", "natural_language_to_sql"]
