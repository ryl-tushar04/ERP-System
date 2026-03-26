import re
from collections import defaultdict

from ..schemas.graph import GraphPayload
from ..services.ai.guardrails import validate_erp_query
from .graph_store import GraphStore, get_graph_store


def _find_first_matching_node_id(question: str, store: GraphStore, node_type: str) -> str | None:
    normalized = question.lower()
    for node in store.get_graph().nodes:
        if node.type != node_type:
            continue
        haystacks = [node.id.lower(), node.label.lower()]
        haystacks.extend(str(value).lower() for value in node.metadata.values())
        if any(token in normalized for token in haystacks):
            return node.id
    return None


def _trace_flow(node_id: str, store: GraphStore) -> GraphPayload:
    frontier = [node_id]
    visited = set(frontier)

    while frontier:
        current = frontier.pop()
        for edge in store.edges_by_node.get(current, []):
            neighbor = edge.target if edge.source == current else edge.source
            if neighbor not in visited:
                visited.add(neighbor)
                frontier.append(neighbor)

    return store.subgraph_for_node_ids(visited)


def _billing_count_by_product(store: GraphStore) -> tuple[str, list[dict[str, int]], GraphPayload]:
    invoice_counts = defaultdict(set)
    graph = store.get_graph()

    order_to_invoices = defaultdict(set)
    delivery_to_order = {}
    invoice_nodes = {node.id for node in graph.nodes if node.type == "invoice"}

    for edge in graph.edges:
        if edge.type == "fulfilled_by":
            delivery_to_order[edge.target] = edge.source
        elif edge.type == "billed_by" and edge.target in invoice_nodes:
            order_id = delivery_to_order.get(edge.source)
            if order_id:
                order_to_invoices[order_id].add(edge.target)

    for edge in graph.edges:
        if edge.type == "contains":
            order_id = edge.source
            product_id = edge.target
            for invoice_id in order_to_invoices.get(order_id, set()):
                invoice_counts[product_id].add(invoice_id)

    rows = []
    for node in graph.nodes:
        if node.type != "product":
            continue
        rows.append(
            {
                "product_id": node.metadata.get("product_id", node.id),
                "product_name": node.label,
                "billing_document_count": len(invoice_counts.get(node.id, set())),
            }
        )

    rows.sort(key=lambda row: row["billing_document_count"], reverse=True)
    top_count = rows[0]["billing_document_count"] if rows else 0
    top_products = [row["product_name"] for row in rows if row["billing_document_count"] == top_count]
    answer = (
        f"The product with the highest number of billing documents is {', '.join(top_products)} "
        f"with {top_count} billing document(s)."
        if rows
        else "No product-to-billing relationships were found in the graph."
    )

    graph_node_ids = {
        node.id
        for node in graph.nodes
        if node.type in {"product", "invoice", "order", "delivery"}
    }
    return answer, rows, store.subgraph_for_node_ids(graph_node_ids)


def _find_incomplete_flows(store: GraphStore) -> tuple[str, list[dict[str, str]], GraphPayload]:
    graph = store.get_graph()
    outgoing = defaultdict(list)
    for edge in graph.edges:
        outgoing[edge.source].append(edge)

    rows = []
    highlighted = set()
    for node in graph.nodes:
        if node.type != "order":
            continue

        order_edges = outgoing.get(node.id, [])
        delivery_edges = [edge for edge in order_edges if edge.type == "fulfilled_by"]
        product_edges = [edge for edge in order_edges if edge.type == "contains"]
        issue = None

        if delivery_edges:
            delivery_id = delivery_edges[0].target
            delivery_outgoing = outgoing.get(delivery_id, [])
            invoice_edges = [edge for edge in delivery_outgoing if edge.type == "billed_by"]
            if not invoice_edges:
                issue = "Delivered but not billed"
        elif product_edges:
            issue = "Open order with no delivery"

        if issue:
            rows.append(
                {
                    "order_id": node.metadata.get("order_id", node.id),
                    "status": node.metadata.get("status", "unknown"),
                    "issue": issue,
                }
            )
            highlighted.add(node.id)
            for edge in order_edges:
                highlighted.add(edge.target)

    answer = (
        f"Found {len(rows)} sales order(s) with broken or incomplete flows."
        if rows
        else "No broken or incomplete order flows were found in the graph."
    )
    return answer, rows, store.subgraph_for_node_ids(highlighted)


def _trace_document_flow(question: str, store: GraphStore) -> tuple[str, list[dict[str, str]], GraphPayload]:
    invoice_node_id = _find_first_matching_node_id(question, store, "invoice")
    if not invoice_node_id:
        raise ValueError("Please specify a billing or invoice document present in the dataset.")

    subgraph = _trace_flow(invoice_node_id, store)
    ordered_types = [
        "customer",
        "address",
        "order",
        "product",
        "plant",
        "delivery",
        "invoice",
        "journal_entry",
        "payment",
    ]
    node_lookup = {node.id: node for node in subgraph.nodes}

    ordered_rows = []
    for node_type in ordered_types:
        for node in subgraph.nodes:
            if node.type == node_type:
                ordered_rows.append(
                    {
                        "entity_type": node.type,
                        "label": node.label,
                        "primary_id": next(iter(node.metadata.values()), node.id),
                    }
                )

    answer = (
        f"Traced the connected ERP flow for {node_lookup[invoice_node_id].label} "
        f"across {len(subgraph.nodes)} related entities."
    )
    return answer, ordered_rows, subgraph


def _invoice_payment_status(store: GraphStore) -> tuple[str, list[dict[str, str]], GraphPayload]:
    graph = store.get_graph()
    outgoing = defaultdict(list)
    nodes_by_id = {node.id: node for node in graph.nodes}

    for edge in graph.edges:
        outgoing[edge.source].append(edge)

    rows = []
    keep_ids = set()

    for node in graph.nodes:
        if node.type != "invoice":
            continue

        payment_edges = [edge for edge in outgoing.get(node.id, []) if edge.type == "settled_by"]
        payment_node = nodes_by_id[payment_edges[0].target] if payment_edges else None
        rows.append(
            {
                "invoice_id": node.metadata.get("invoice_id", node.id),
                "invoice_label": node.label,
                "invoice_cancelled": str(node.metadata.get("cancelled", False)),
                "payment_status": "paid" if payment_node else "unpaid",
                "payment_id": payment_node.metadata.get("payment_id") if payment_node else None,
                "payment_amount": payment_node.metadata.get("amount") if payment_node else None,
            }
        )
        keep_ids.add(node.id)
        if payment_node:
            keep_ids.add(payment_node.id)

    rows.sort(key=lambda row: row["invoice_id"])
    answer = f"Found payment status for {len(rows)} billing document(s)."
    return answer, rows, store.subgraph_for_node_ids(keep_ids)


def answer_graph_query(question: str, store: GraphStore | None = None) -> dict:
    validated_question = validate_erp_query(question)
    store = store or get_graph_store()
    normalized = validated_question.lower()

    if "highest" in normalized and ("billing" in normalized or "invoice" in normalized) and "product" in normalized:
        answer, rows, subgraph = _billing_count_by_product(store)
        return {"answer": answer, "data": rows, "graph": subgraph, "sql": None}

    if "invoice" in normalized and "payment" in normalized and "status" in normalized:
        answer, rows, subgraph = _invoice_payment_status(store)
        return {"answer": answer, "data": rows, "graph": subgraph, "sql": None}

    if any(token in normalized for token in ("broken", "incomplete")):
        answer, rows, subgraph = _find_incomplete_flows(store)
        return {"answer": answer, "data": rows, "graph": subgraph, "sql": None}

    if "trace" in normalized or "flow" in normalized:
        answer, rows, subgraph = _trace_document_flow(validated_question, store)
        return {"answer": answer, "data": rows, "graph": subgraph, "sql": None}

    matches = store.search_nodes(validated_question)
    if matches:
        node_ids = {node.id for node in matches}
        subgraph = store.subgraph_for_node_ids(node_ids)
        rows = [
            {
                "id": node.id,
                "type": node.type,
                "label": node.label,
            }
            for node in matches
        ]
        answer = f"Found {len(matches)} graph entity match(es) related to your question."
        return {"answer": answer, "data": rows, "graph": subgraph, "sql": None}

    raise ValueError(
        "This system is designed to answer questions related to the provided dataset only."
    )
