const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
const QUERY_API_URL = `${API_BASE_URL}/api/v1/query`;
const GRAPH_API_URL = `${API_BASE_URL}/api/v1/graph`;

export async function runErpQuery(query) {
  const trimmedQuery = query.trim();
  if (!trimmedQuery) {
    throw new Error("Query must not be empty.");
  }

  const response = await fetch(QUERY_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ query: trimmedQuery }),
  });

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.detail || "Failed to run query.");
  }

  return {
    answer: payload.answer || "",
    sql: payload.sql || "",
    data: payload.data ?? [],
    graph: payload.graph ?? { nodes: [], edges: [] },
  };
}

export async function fetchGraph() {
  const response = await fetch(GRAPH_API_URL);
  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(payload.detail || "Failed to load graph.");
  }

  return {
    nodes: payload.nodes ?? [],
    edges: payload.edges ?? [],
  };
}
