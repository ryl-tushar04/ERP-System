import re

_ERP_KEYWORDS = {
    "erp",
    "order",
    "orders",
    "sales",
    "billing",
    "document",
    "delivery",
    "deliveries",
    "invoice",
    "invoices",
    "payment",
    "payments",
    "customer",
    "customers",
    "product",
    "products",
    "address",
    "addresses",
    "plant",
    "material",
    "journal",
    "flow",
    "graph",
    "workflow",
    "status",
}
_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def validate_erp_query(prompt: str) -> str:
    sanitized = prompt.strip()
    if not sanitized:
        raise ValueError("Prompt must not be empty.")

    tokens = {token.lower() for token in _TOKEN_PATTERN.findall(sanitized)}
    if not tokens.intersection(_ERP_KEYWORDS):
        raise ValueError("Only ERP-related queries are allowed.")

    return sanitized


def validate_prompt(prompt: str) -> str:
    return validate_erp_query(prompt)
