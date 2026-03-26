import json
from functools import lru_cache
from pathlib import Path

from ..schemas.graph import GraphEdge, GraphNode, GraphNodeDetail, GraphPayload


class GraphStore:
    def __init__(self, graph: GraphPayload):
        self.graph = graph
        self.nodes_by_id = {node.id: node for node in graph.nodes}
        self.edges_by_node: dict[str, list[GraphEdge]] = {}
        for edge in graph.edges:
            self.edges_by_node.setdefault(edge.source, []).append(edge)
            self.edges_by_node.setdefault(edge.target, []).append(edge)

    def get_graph(self) -> GraphPayload:
        return self.graph

    def get_node_detail(self, node_id: str) -> GraphNodeDetail:
        node = self.nodes_by_id[node_id]
        edges = self.edges_by_node.get(node_id, [])
        neighbor_ids = {
            edge.target if edge.source == node_id else edge.source
            for edge in edges
        }
        neighbors = [self.nodes_by_id[neighbor_id] for neighbor_id in neighbor_ids]
        return GraphNodeDetail(node=node, neighbors=neighbors, edges=edges)

    def search_nodes(self, query: str) -> list[GraphNode]:
        normalized = query.strip().lower()
        if not normalized:
            return []

        results = []
        for node in self.graph.nodes:
            haystacks = [node.label.lower(), node.type.lower()]
            haystacks.extend(str(value).lower() for value in node.metadata.values())
            if any(normalized in haystack for haystack in haystacks):
                results.append(node)
        return results

    def subgraph_for_node_ids(self, node_ids: set[str]) -> GraphPayload:
        if not node_ids:
            return GraphPayload(nodes=[], edges=[])

        edges = [
            edge
            for edge in self.graph.edges
            if edge.source in node_ids and edge.target in node_ids
        ]
        nodes = [self.nodes_by_id[node_id] for node_id in node_ids if node_id in self.nodes_by_id]
        return GraphPayload(nodes=nodes, edges=edges)


def _load_graph_payload() -> GraphPayload:
    project_root = Path(__file__).resolve().parents[3]
    return _load_payload_from_candidates(
        [
            project_root / "data" / "graph.json",
            project_root / "data" / "sample_graph.json",
        ]
    )


def _load_payload_from_candidates(candidate_paths: list[Path]) -> GraphPayload:
    for path in candidate_paths:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return GraphPayload(
                nodes=[GraphNode(**node) for node in payload.get("nodes", [])],
                edges=[GraphEdge(**edge) for edge in payload.get("edges", [])],
            )

    return GraphPayload(nodes=[], edges=[])


@lru_cache
def get_graph_store() -> GraphStore:
    return GraphStore(_load_graph_payload())


@lru_cache
def get_overview_graph_store() -> GraphStore:
    project_root = Path(__file__).resolve().parents[3]
    return GraphStore(
        _load_payload_from_candidates(
            [
                project_root / "data" / "graph_overview.json",
                project_root / "data" / "graph.json",
                project_root / "data" / "sample_graph.json",
            ]
        )
    )
