import { useEffect, useState } from "react";
import QueryGraph from "./QueryGraph";
import { fetchGraph, runErpQuery } from "./api";

const initialResult = {
  answer: "",
  sql: "",
  data: null,
  graph: { nodes: [], edges: [] },
};

export default function App() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(initialResult);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const hasResult = Array.isArray(result.data);

  useEffect(() => {
    if (Array.isArray(result.data) && result.data.length > 0) {
      window.scrollTo({ top: 500, behavior: "smooth" });
    }
  }, [result.data]);

  useEffect(() => {
    async function loadGraph() {
      try {
        const payload = await fetchGraph();
        setGraph(payload);
      } catch (graphError) {
        setError(graphError.message || "Failed to load graph.");
      }
    }

    loadGraph();
  }, []);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      const payload = await runErpQuery(query);
      setResult(payload);
      if (payload.graph?.nodes?.length) {
        setGraph(payload.graph);
      }
    } catch (requestError) {
      setResult(initialResult);
      setError(requestError.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={styles.page}>
      <section style={styles.shell}>
        <section style={styles.hero}>
          <div>
            <p style={styles.eyebrow}>ERP Workflow Assistant</p>
            <h1 style={styles.title}>Explore ERP workflow relationships as a graph</h1>
            <p style={styles.subtitle}>
              Ask a business question, inspect the grounded answer, and explore the connected
              orders, deliveries, invoices, payments, customers, products, and addresses.
            </p>
          </div>
          <div style={styles.tipCard}>
            <p style={styles.tipLabel}>Example</p>
            <p style={styles.tipText}>
              Trace the full flow of invoice INV-9001 or find sales orders with incomplete flows
            </p>
          </div>
        </section>

        <section style={styles.card}>
          <form onSubmit={handleSubmit} style={styles.form}>
            <label htmlFor="erp-query" style={styles.label}>
              Natural language query
            </label>
            <textarea
              id="erp-query"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Example: Show all invoices with their payment status"
              rows={5}
              style={styles.textarea}
            />
            <p style={styles.examples}>
              Examples:
              <br />
              - Which products are associated with the highest number of billing documents?
              <br />
              - Trace the full flow of invoice INV-9001
              <br />
              - Identify sales orders with broken or incomplete flows
            </p>

            <div style={styles.formFooter}>
              <p style={styles.helperText}>Only ERP-related questions are accepted.</p>
              <button type="submit" disabled={loading || !query.trim()} style={styles.button}>
                {loading ? "Running query..." : "Run Query"}
              </button>
            </div>
          </form>

          {loading ? <div style={styles.loading}>Generating SQL and fetching results...</div> : null}
          {error ? <div style={styles.error}>{error}</div> : null}

          <section style={styles.resultsGrid}>
            <section style={{ ...styles.panel, gridColumn: "1 / -1" }}>
              <div style={styles.panelHeader}>
                <h2 style={styles.panelTitle}>Answer</h2>
                <span style={styles.badge}>{result.answer ? "Grounded" : "Waiting"}</span>
              </div>
              <div style={styles.answerBox}>
                {result.answer || "A grounded answer will appear here after you run a query."}
              </div>
            </section>

            <section style={styles.panel}>
              <div style={styles.panelHeader}>
                <h2 style={styles.panelTitle}>Generated SQL</h2>
                <span style={styles.badge}>{result.sql ? "SQL used" : "Graph mode"}</span>
              </div>
              <pre style={styles.pre}>{result.sql || "No SQL executed for this graph-backed answer."}</pre>
            </section>

            <section style={styles.panel}>
              <div style={styles.panelHeader}>
                <h2 style={styles.panelTitle}>JSON Result</h2>
                <span style={styles.badge}>
                  {hasResult ? `${result.data.length} row${result.data.length === 1 ? "" : "s"}` : "No data"}
                </span>
              </div>
              <pre style={styles.pre}>
                {hasResult
                  ? JSON.stringify(result.data, null, 2)
                  : "Query results will appear here."}
              </pre>
            </section>

            <section style={{ ...styles.panel, gridColumn: "1 / -1" }}>
              <div style={styles.panelHeader}>
                <h2 style={styles.panelTitle}>Graph View</h2>
                <span style={styles.badge}>
                  {graph.nodes.length} node{graph.nodes.length === 1 ? "" : "s"}
                </span>
              </div>
              <QueryGraph graph={graph} />
            </section>
          </section>
        </section>
      </section>
    </main>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    margin: 0,
    background:
      "radial-gradient(circle at top, rgba(45, 118, 232, 0.12), transparent 30%), #f4f7fb",
    color: "#172033",
    fontFamily: "Segoe UI, sans-serif",
    padding: "48px 20px",
  },
  shell: {
    maxWidth: "1100px",
    margin: "0 auto",
    display: "grid",
    gap: "24px",
  },
  hero: {
    display: "grid",
    gap: "20px",
    alignItems: "start",
    gridTemplateColumns: "minmax(0, 1fr) minmax(240px, 300px)",
  },
  eyebrow: {
    margin: "0 0 10px",
    fontSize: "12px",
    letterSpacing: "0.12em",
    textTransform: "uppercase",
    color: "#1f5eff",
    fontWeight: 700,
  },
  card: {
    background: "#ffffff",
    border: "1px solid #d7dfeb",
    borderRadius: "20px",
    padding: "28px",
    boxShadow: "0 18px 50px rgba(19, 33, 68, 0.08)",
  },
  title: {
    margin: "0 0 10px",
    fontSize: "38px",
    lineHeight: 1.1,
  },
  subtitle: {
    margin: 0,
    color: "#52607a",
    lineHeight: 1.5,
    maxWidth: "700px",
  },
  tipCard: {
    background: "#0f172a",
    color: "#dbe7ff",
    borderRadius: "18px",
    padding: "18px",
    minHeight: "100%",
  },
  tipLabel: {
    margin: "0 0 10px",
    color: "#8fb4ff",
    fontSize: "12px",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    fontWeight: 700,
  },
  tipText: {
    margin: 0,
    lineHeight: 1.6,
  },
  form: {
    display: "grid",
    gap: "14px",
    marginBottom: "18px",
  },
  label: {
    fontSize: "14px",
    fontWeight: 700,
  },
  textarea: {
    width: "100%",
    resize: "vertical",
    minHeight: "132px",
    borderRadius: "14px",
    border: "1px solid #c7d2e3",
    padding: "16px",
    fontSize: "15px",
    lineHeight: 1.5,
    outline: "none",
    boxSizing: "border-box",
    background: "#fbfcff",
  },
  formFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
    flexWrap: "wrap",
  },
  helperText: {
    margin: 0,
    color: "#66748d",
    fontSize: "14px",
  },
  examples: {
    margin: 0,
    color: "#66748d",
    fontSize: "13px",
    lineHeight: 1.6,
  },
  button: {
    width: "fit-content",
    border: 0,
    borderRadius: "12px",
    padding: "12px 20px",
    background: "#1f5eff",
    color: "#ffffff",
    fontSize: "15px",
    fontWeight: 600,
    cursor: "pointer",
    boxShadow: "0 10px 24px rgba(31, 94, 255, 0.22)",
  },
  loading: {
    marginBottom: "18px",
    padding: "13px 14px",
    borderRadius: "12px",
    background: "#eef4ff",
    color: "#1d4ed8",
    border: "1px solid #c9dafc",
  },
  error: {
    marginBottom: "18px",
    padding: "13px 14px",
    borderRadius: "12px",
    background: "#fff1f1",
    color: "#b42318",
    border: "1px solid #f3c7c7",
  },
  resultsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "18px",
    alignItems: "start",
  },
  panel: {
    border: "1px solid #d9e2ef",
    borderRadius: "16px",
    padding: "16px",
    background: "#fcfdff",
  },
  panelHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    gap: "12px",
    marginBottom: "12px",
  },
  panelTitle: {
    margin: 0,
    fontSize: "18px",
  },
  badge: {
    padding: "6px 10px",
    borderRadius: "999px",
    background: "#edf2ff",
    color: "#3659a6",
    fontSize: "12px",
    fontWeight: 700,
    whiteSpace: "nowrap",
  },
  pre: {
    margin: 0,
    padding: "16px",
    borderRadius: "12px",
    background: "#0f172a",
    color: "#dbe7ff",
    overflowX: "auto",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    fontSize: "14px",
    lineHeight: 1.6,
  },
  answerBox: {
    borderRadius: "12px",
    border: "1px solid #d9e2ef",
    background: "#f8fbff",
    padding: "16px",
    color: "#172033",
    lineHeight: 1.6,
    fontSize: "15px",
  },
};
