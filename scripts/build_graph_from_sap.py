import argparse
import json
from collections import defaultdict
from pathlib import Path


DEFAULT_DATASET_ROOT = Path(r"C:\Users\tusha\Downloads\sap-order-to-cash-dataset\sap-o2c-data")


def iter_jsonl_records(directory: Path):
    for path in sorted(directory.glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    yield json.loads(line)


def add_node(nodes, node_index, node_id, node_type, label, metadata):
    if node_id not in node_index:
        node_index.add(node_id)
        nodes.append(
            {
                "id": node_id,
                "type": node_type,
                "label": label,
                "metadata": metadata,
            }
        )


def add_edge(edges, edge_index, source, target, edge_type, label, metadata=None):
    edge_id = f"{source}|{edge_type}|{target}"
    if edge_id not in edge_index:
        edge_index.add(edge_id)
        edges.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "type": edge_type,
                "label": label,
                "metadata": metadata or {},
            }
        )


def build_graph(dataset_root: Path):
    product_descriptions = {}
    for record in iter_jsonl_records(dataset_root / "product_descriptions"):
        if record.get("language") == "EN":
            product_descriptions[record["product"]] = record.get("productDescription") or record["product"]

    customers = {}
    for record in iter_jsonl_records(dataset_root / "business_partners"):
        customer_id = record.get("customer") or record.get("businessPartner")
        if customer_id:
            customers[customer_id] = record

    addresses = {}
    for record in iter_jsonl_records(dataset_root / "business_partner_addresses"):
        customer_id = record.get("businessPartner")
        if customer_id and customer_id not in addresses:
            addresses[customer_id] = record

    plants = {record["plant"]: record for record in iter_jsonl_records(dataset_root / "plants")}
    products = {record["product"]: record for record in iter_jsonl_records(dataset_root / "products")}
    sales_orders = {record["salesOrder"]: record for record in iter_jsonl_records(dataset_root / "sales_order_headers")}
    deliveries = {
        record["deliveryDocument"]: record
        for record in iter_jsonl_records(dataset_root / "outbound_delivery_headers")
    }
    invoices = {
        record["billingDocument"]: record
        for record in iter_jsonl_records(dataset_root / "billing_document_headers")
    }

    order_items_by_order = defaultdict(list)
    for record in iter_jsonl_records(dataset_root / "sales_order_items"):
        order_items_by_order[record["salesOrder"]].append(record)

    delivery_items_by_delivery = defaultdict(list)
    deliveries_by_order = defaultdict(set)
    for record in iter_jsonl_records(dataset_root / "outbound_delivery_items"):
        delivery_items_by_delivery[record["deliveryDocument"]].append(record)
        order_id = record.get("referenceSdDocument")
        if order_id:
            deliveries_by_order[order_id].add(record["deliveryDocument"])

    invoice_items_by_invoice = defaultdict(list)
    invoices_by_delivery = defaultdict(set)
    for record in iter_jsonl_records(dataset_root / "billing_document_items"):
        invoice_items_by_invoice[record["billingDocument"]].append(record)
        delivery_id = record.get("referenceSdDocument")
        if delivery_id:
            invoices_by_delivery[delivery_id].add(record["billingDocument"])

    journal_entries = {}
    for record in iter_jsonl_records(dataset_root / "journal_entry_items_accounts_receivable"):
        document_id = record.get("accountingDocument")
        if document_id and document_id not in journal_entries:
            journal_entries[document_id] = record

    payments = {}
    for record in iter_jsonl_records(dataset_root / "payments_accounts_receivable"):
        document_id = record.get("accountingDocument")
        if document_id and document_id not in payments:
            payments[document_id] = record

    nodes = []
    edges = []
    node_index = set()
    edge_index = set()

    for order_id, order in sales_orders.items():
        order_node_id = f"order-{order_id}"
        add_node(
            nodes,
            node_index,
            order_node_id,
            "order",
            f"Sales Order {order_id}",
            {
                "order_id": order_id,
                "status": order.get("overallDeliveryStatus"),
                "billing_status": order.get("overallOrdReltdBillgStatus"),
                "customer_id": order.get("soldToParty"),
                "requested_delivery_date": order.get("requestedDeliveryDate"),
                "total_net_amount": order.get("totalNetAmount"),
            },
        )

        customer_id = order.get("soldToParty")
        if customer_id:
            customer = customers.get(customer_id, {})
            customer_node_id = f"customer-{customer_id}"
            add_node(
                nodes,
                node_index,
                customer_node_id,
                "customer",
                customer.get("businessPartnerName") or f"Customer {customer_id}",
                {
                    "customer_id": customer_id,
                    "blocked": customer.get("businessPartnerIsBlocked"),
                    "archived": customer.get("isMarkedForArchiving"),
                },
            )
            add_edge(edges, edge_index, customer_node_id, order_node_id, "placed", "placed")

            address = addresses.get(customer_id)
            if address:
                address_node_id = f"address-{address['addressId']}"
                city = address.get("cityName") or address.get("region") or address["addressId"]
                add_node(
                    nodes,
                    node_index,
                    address_node_id,
                    "address",
                    city,
                    {
                        "address_id": address["addressId"],
                        "street": address.get("streetName"),
                        "city": address.get("cityName"),
                        "postal_code": address.get("postalCode"),
                        "country": address.get("country"),
                    },
                )
                add_edge(
                    edges,
                    edge_index,
                    customer_node_id,
                    address_node_id,
                    "located_at",
                    "located at",
                )

        for item in order_items_by_order.get(order_id, []):
            material_id = item.get("material")
            if material_id:
                product = products.get(material_id, {})
                product_node_id = f"product-{material_id}"
                add_node(
                    nodes,
                    node_index,
                    product_node_id,
                    "product",
                    product_descriptions.get(material_id) or product.get("productOldId") or material_id,
                    {
                        "product_id": material_id,
                        "product_group": product.get("productGroup") or item.get("materialGroup"),
                        "base_unit": product.get("baseUnit") or item.get("requestedQuantityUnit"),
                    },
                )
                add_edge(edges, edge_index, order_node_id, product_node_id, "contains", "contains")

            plant_id = item.get("productionPlant")
            if plant_id:
                plant = plants.get(plant_id, {})
                plant_node_id = f"plant-{plant_id}"
                add_node(
                    nodes,
                    node_index,
                    plant_node_id,
                    "plant",
                    plant.get("plantName") or f"Plant {plant_id}",
                    {
                        "plant_id": plant_id,
                        "sales_organization": plant.get("salesOrganization"),
                        "distribution_channel": plant.get("distributionChannel"),
                    },
                )
                add_edge(edges, edge_index, order_node_id, plant_node_id, "sourced_from", "sourced from")

        for delivery_id in deliveries_by_order.get(order_id, set()):
            delivery = deliveries.get(delivery_id, {})
            delivery_node_id = f"delivery-{delivery_id}"
            add_node(
                nodes,
                node_index,
                delivery_node_id,
                "delivery",
                f"Delivery {delivery_id}",
                {
                    "delivery_id": delivery_id,
                    "goods_movement_status": delivery.get("overallGoodsMovementStatus"),
                    "picking_status": delivery.get("overallPickingStatus"),
                    "shipping_point": delivery.get("shippingPoint"),
                },
            )
            add_edge(edges, edge_index, order_node_id, delivery_node_id, "fulfilled_by", "fulfilled by")

            for delivery_item in delivery_items_by_delivery.get(delivery_id, []):
                plant_id = delivery_item.get("plant")
                if plant_id:
                    plant = plants.get(plant_id, {})
                    plant_node_id = f"plant-{plant_id}"
                    add_node(
                        nodes,
                        node_index,
                        plant_node_id,
                        "plant",
                        plant.get("plantName") or f"Plant {plant_id}",
                        {
                            "plant_id": plant_id,
                            "sales_organization": plant.get("salesOrganization"),
                            "distribution_channel": plant.get("distributionChannel"),
                        },
                    )
                    add_edge(
                        edges,
                        edge_index,
                        delivery_node_id,
                        plant_node_id,
                        "ships_from",
                        "ships from",
                    )

            for invoice_id in invoices_by_delivery.get(delivery_id, set()):
                invoice = invoices.get(invoice_id, {})
                invoice_node_id = f"invoice-{invoice_id}"
                add_node(
                    nodes,
                    node_index,
                    invoice_node_id,
                    "invoice",
                    f"Billing {invoice_id}",
                    {
                        "invoice_id": invoice_id,
                        "cancelled": invoice.get("billingDocumentIsCancelled"),
                        "accounting_document": invoice.get("accountingDocument"),
                        "sold_to_party": invoice.get("soldToParty"),
                        "total_net_amount": invoice.get("totalNetAmount"),
                    },
                )
                add_edge(edges, edge_index, delivery_node_id, invoice_node_id, "billed_by", "billed by")

                journal_id = invoice.get("accountingDocument")
                if journal_id:
                    journal = journal_entries.get(journal_id, {})
                    journal_node_id = f"journal-{journal_id}"
                    add_node(
                        nodes,
                        node_index,
                        journal_node_id,
                        "journal_entry",
                        f"Journal Entry {journal_id}",
                        {
                            "journal_entry_id": journal_id,
                            "posting_date": journal.get("postingDate"),
                            "reference_document": journal.get("referenceDocument"),
                            "amount": journal.get("amountInTransactionCurrency"),
                            "currency": journal.get("transactionCurrency"),
                        },
                    )
                    add_edge(edges, edge_index, invoice_node_id, journal_node_id, "posted_to", "posted to")

                    payment = payments.get(journal_id)
                    if payment:
                        payment_node_id = f"payment-{journal_id}"
                        add_node(
                            nodes,
                            node_index,
                            payment_node_id,
                            "payment",
                            f"Payment {journal_id}",
                            {
                                "payment_id": journal_id,
                                "customer_id": payment.get("customer"),
                                "clearing_date": payment.get("clearingDate"),
                                "amount": payment.get("amountInTransactionCurrency"),
                                "currency": payment.get("transactionCurrency"),
                            },
                        )
                        add_edge(edges, edge_index, invoice_node_id, payment_node_id, "settled_by", "settled by")

    return {"nodes": nodes, "edges": edges}


def build_overview_graph(full_graph: dict, max_orders: int = 35):
    order_nodes = [node for node in full_graph["nodes"] if node["type"] == "order"][:max_orders]
    keep_ids = {node["id"] for node in order_nodes}

    expanded = True
    while expanded:
        expanded = False
        for edge in full_graph["edges"]:
            if edge["source"] in keep_ids or edge["target"] in keep_ids:
                if edge["source"] not in keep_ids or edge["target"] not in keep_ids:
                    expanded = True
                keep_ids.add(edge["source"])
                keep_ids.add(edge["target"])

    nodes = [node for node in full_graph["nodes"] if node["id"] in keep_ids]
    edges = [
        edge
        for edge in full_graph["edges"]
        if edge["source"] in keep_ids and edge["target"] in keep_ids
    ]
    return {"nodes": nodes, "edges": edges}


def main():
    parser = argparse.ArgumentParser(description="Build ERP graph JSON from SAP O2C JSONL dataset.")
    parser.add_argument("--dataset-root", type=Path, default=DEFAULT_DATASET_ROOT)
    parser.add_argument("--output", type=Path, default=Path("erp-system/data/graph.json"))
    parser.add_argument("--overview-output", type=Path, default=Path("erp-system/data/graph_overview.json"))
    args = parser.parse_args()

    full_graph = build_graph(args.dataset_root)
    overview_graph = build_overview_graph(full_graph)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(full_graph, handle, ensure_ascii=True)

    with args.overview_output.open("w", encoding="utf-8") as handle:
        json.dump(overview_graph, handle, ensure_ascii=True)

    print(
        json.dumps(
            {
                "full_nodes": len(full_graph["nodes"]),
                "full_edges": len(full_graph["edges"]),
                "overview_nodes": len(overview_graph["nodes"]),
                "overview_edges": len(overview_graph["edges"]),
                "output": str(args.output.resolve()),
                "overview_output": str(args.overview_output.resolve()),
            }
        )
    )


if __name__ == "__main__":
    main()
