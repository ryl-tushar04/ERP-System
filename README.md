# ERP Workflow Debugging System

This project is a graph-based ERP debugging and exploration system built for forward-deployed workflows. It lets a user explore connected business entities, ask natural-language questions about the dataset, and receive grounded answers backed by graph traversal or validated SQL execution.

The system is designed around one principle: constrained, inspectable intelligence. The model is never treated as an authority on its own. It operates inside a bounded pipeline with domain guardrails, explicit graph structure, and visible outputs.

Deployed Link: https://erp-system-ryl-tushar04s-projects.vercel.app/

## What The System Does

- Builds and serves a context graph of ERP entities
- Visualizes interconnected nodes such as orders, deliveries, invoices, payments, customers, products, and addresses
- Accepts natural-language questions through a query interface
- Answers from the dataset, either through graph-backed reasoning or SQL when configured
- Rejects unrelated or off-domain prompts

## Runtime Modes

The repo currently supports two modes:

- `Seeded graph mode`
  Uses `data/sample_graph.json` so the system works immediately out of the box.
- `Dataset graph mode`
  Loads `data/graph.json` when you convert the provided assignment dataset into nodes and edges.
- `LLM mode`
  Uses Groq by default when `GROQ_API_KEY` is configured, with OpenAI-compatible client wiring.

This means the application is runnable now, while still having a clear path to swap in the real dataset for final submission.

## Architecture

```text
React UI
  -> GET /api/v1/graph
  -> POST /api/v1/query
  -> FastAPI orchestration layer
  -> ERP guardrails
  -> Graph-backed reasoning
  -> Optional LLM SQL generation
  -> Optional PostgreSQL execution
  -> JSON response with answer, sql, data, graph
  -> Cytoscape graph visualization
```

## Why This Design

The assignment is fundamentally about system modeling and grounded queryability, not just chat. For that reason, the system is split into three layers:

1. `Graph layer`
   The business workflow is represented as explicit nodes and edges so entity relationships can be inspected directly.
2. `Query layer`
   Natural language is translated into bounded operations over the graph and, when enabled, into validated SQL.
3. `Presentation layer`
   The UI exposes the graph, the answer, the supporting records, and the generated SQL when available.

This keeps the system explainable under debugging conditions.

## Reliability Model

- The backend can answer in graph mode even when no database or API key is configured
- SQL execution is read-only and restricted to validated `SELECT` or `WITH` queries
- PostgreSQL access uses connection pooling to avoid connection churn
- Query execution is separate from graph reasoning so failures can be isolated cleanly
- The frontend always shows the supporting graph and data, which makes answers auditable

## LLM Control Strategy

The LLM path is deliberately constrained to reduce hallucination.

- Prompt scope is limited to known ERP workflow entities
- Join behavior is explicitly described in the SQL generation prompt
- Output is constrained to SQL only
- Generated SQL is validated before execution
- Unrelated prompts are rejected before they reach the model
- If SQL execution is unavailable or fails, the system falls back to graph-grounded reasoning instead of returning an invented answer

This creates a layered control model:

1. Domain guardrails restrict off-topic prompts
2. The model receives explicit schema and join rules
3. SQL validation blocks unsafe or unknown output
4. The system returns only dataset-backed results

## Graph Modeling

The graph centers on lifecycle dependencies across the ERP flow:

- Customer -> Order
- Order -> Delivery
- Delivery -> Invoice
- Invoice -> Payment
- Customer -> Address
- Order -> Product

This is intentionally simple, because clarity of relationship modeling matters more than graph complexity for this assignment.

## Query Workflow

The query path is built for debugging and inspection:

1. The user asks a question in natural language
2. The system validates that the question is ERP-related
3. The backend answers either through graph reasoning or validated SQL
4. The response returns:
   - a grounded natural-language answer
   - SQL, if SQL was used
   - supporting tabular records
   - a graph or subgraph for exploration

This makes it possible to answer questions like:

- Which products are associated with the highest number of billing documents?
- Trace the full flow of a billing document
- Identify orders with incomplete flows

## Trade-offs

- The seeded graph makes the app immediately runnable, but the strongest final submission should replace it with the provided dataset-derived graph
- Graph-backed heuristics are more reliable than unconstrained generation, but less flexible than a fully general semantic planner
- The current SQL path is useful for transparency, but the graph path is the more robust default for this repo as it stands
- Guardrails are intentionally simple and auditable, but conservative by design

## Backend Structure

```text
backend/
  main.py                 FastAPI entrypoint wrapper
  app/
    main.py               FastAPI application factory
    query_engine.py       PostgreSQL pooling and query execution
    llm.py                Natural language to SQL translation
    guardrails.py         Public validation exports
    services/
      graph_store.py      Graph loading and retrieval
      query_service.py    Graph-backed question answering
      ai/                 OpenAI client and prompt validation
    api/v1/endpoints/
      health.py
      graph.py
      query.py
    schemas/
      graph.py
      query.py
```

## Frontend Structure

```text
frontend/
  index.html              Vite entry HTML
  package.json            React and Cytoscape dependencies
  src/
    main.jsx              React bootstrap
    App.jsx               Query and graph exploration UI
    api.js                Backend API client
    QueryGraph.jsx        Context graph visualization
```

## Data Hand-Off

To plug in the real assignment dataset, convert it into this shape and save it as `data/graph.json`:

```json
{
  "nodes": [
    { "id": "order-so-1001", "type": "order", "label": "Sales Order SO-1001", "metadata": {} }
  ],
  "edges": [
    { "id": "edge-1", "source": "order-so-1001", "target": "delivery-del-501", "type": "fulfilled_by", "label": "fulfilled by" }
  ]
}
```

The app automatically prefers `data/graph.json` and falls back to `data/sample_graph.json` only when the real graph file is absent.

## LLM Configuration

The repo is wired to use Groq as the default hosted LLM provider.

```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=your_groq_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

If no LLM key is configured, the system falls back to graph-backed reasoning only.

## Local Run

```bash
# backend
pip install -r requirements.txt
uvicorn main:app --reload

# frontend
cd erp-system/frontend
npm install
npm run dev
```

## Why This System Exists

ERP issues are usually not isolated record problems. They are broken flows across multiple linked entities. A useful debugging system therefore needs more than a chatbot. It needs explicit relationship modeling, bounded query logic, and outputs that engineers can verify under pressure.

This project is built to satisfy that need.
