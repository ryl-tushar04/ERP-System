# ERP Workflow Debugging System

This project is a graph-based ERP workflow exploration and debugging system built for the Forward Deployed Engineer assignment. It ingests fragmented SAP order-to-cash data, models the business flow as a graph, exposes a natural-language query interface, and returns grounded answers backed by graph traversal and optional SQL generation.

The system is designed around constrained intelligence rather than autonomous intelligence. The model is treated as a bounded translation layer inside a controlled pipeline with explicit graph structure, domain guardrails, and inspectable outputs.

Deployed Link: https://erp-system-ryl-tushar04s-projects.vercel.app/

## What The System Does

- Ingests SAP O2C data and converts it into an entity graph
- Visualizes interconnected ERP entities such as:
  - sales orders
  - deliveries
  - billing documents
  - payments
  - customers
  - products
  - plants
  - addresses
  - journal entries
- Accepts natural-language questions through a query interface
- Answers from the dataset using:
  - graph-backed reasoning by default
  - optional LLM-assisted SQL generation when configured
- Rejects unrelated or off-domain prompts

## Deployment Shape

The system is intended to be deployed as:

- Backend API on Render
- Frontend UI on Vercel

This keeps the architecture simple and gives a clean public demo surface:

- Render hosts the FastAPI graph/query API
- Vercel hosts the React interface and calls the backend over HTTPS

## Architecture

```text
React UI (Vercel)
  -> GET /api/v1/graph
  -> GET /api/v1/graph/search
  -> GET /api/v1/graph/nodes/{node_id}
  -> POST /api/v1/query
  -> FastAPI backend (Render)
  -> ERP guardrails
  -> Graph-backed reasoning
  -> Optional Groq-powered SQL generation
  -> Optional PostgreSQL execution
  -> JSON response with answer, sql, data, graph
  -> Cytoscape graph visualization
```

## Core Design Decisions

### 1. Graph-first modeling

The assignment is fundamentally about tracing fragmented relationships across business entities. For that reason, the system is graph-first rather than chatbot-first.

Key graph relationships include:

- Customer -> Order
- Order -> Delivery
- Delivery -> Invoice
- Invoice -> Payment
- Invoice -> Journal Entry
- Order -> Product
- Order -> Plant
- Customer -> Address

This makes the workflow inspectable directly rather than hiding the business flow behind a generated answer.

### 2. Graph-backed answers before SQL

The system answers from graph data by default. This keeps the application useful even when:

- a live relational database is not available
- an LLM API key is not configured
- SQL generation fails

When LLM access is configured, the SQL path becomes an enhancement rather than a hard dependency.

### 3. Constrained LLM usage

The LLM is used only as a bounded query translation layer.

- domain prompts are restricted to ERP data
- SQL generation is limited to known tables
- output is constrained to SQL only
- generated SQL is validated before execution
- the system falls back to graph-backed reasoning when SQL execution is unavailable or fails

This is intentionally safer than a free-form conversational agent.

## Reliability Model

- The backend works without a database in graph-backed mode
- The backend works without an LLM key in graph-backed mode
- SQL execution is restricted to validated read-only queries
- PostgreSQL access uses pooling
- Query answering is separated from graph loading, which makes failure domains easier to reason about
- The frontend always exposes the supporting graph and records, which makes answers auditable

## Graph Construction

The project includes a real ingestion pipeline for the provided SAP dataset.

Dataset path used during development:

`C:\Users\tusha\Downloads\sap-order-to-cash-dataset\sap-o2c-data`

The ingestion script reads the JSONL partitions and generates:

- `data/graph.json`
- `data/graph_overview.json`

The generated graph currently contains:

- 724 nodes
- 993 edges

### Ingestion Script

`scripts/build_graph_from_sap.py`

This script maps:

- `sales_order_headers` -> order nodes
- `business_partners` -> customer nodes
- `business_partner_addresses` -> address nodes
- `sales_order_items` -> product and plant relationships
- `outbound_delivery_headers/items` -> delivery nodes and order links
- `billing_document_headers/items` -> invoice nodes and delivery links
- `journal_entry_items_accounts_receivable` -> journal entry nodes
- `payments_accounts_receivable` -> payment nodes

## Runtime Modes

The repo supports three practical modes:

### 1. Sample graph mode

Uses `data/sample_graph.json` so the app can boot even without the real dataset.

### 2. Real graph mode

Uses `data/graph.json` generated from the SAP dataset.

### 3. LLM mode

Uses Groq by default when `GROQ_API_KEY` is configured, via an OpenAI-compatible API client.

## Query Workflow

1. The user asks a question in natural language
2. The system validates that the question is ERP-related
3. The backend answers either through:
   - graph reasoning
   - LLM-assisted SQL generation
4. The response returns:
   - a grounded natural-language answer
   - SQL, if SQL was used
   - supporting rows
   - a graph or subgraph for visualization

Example supported questions:

- Which products are associated with the highest number of billing documents?
- Trace the full flow of a billing document
- Identify sales orders with broken or incomplete flows
- Show all invoices with their payment status

## Guardrails

The system must stay within the provided dataset and ERP domain.

Current guardrails:

- reject empty prompts
- reject unrelated prompts
- restrict prompt interpretation to ERP entities such as:
  - orders
  - deliveries
  - invoices
  - payments
  - products
  - customers
  - plants
  - billing documents
  - journal entries
- restrict SQL generation to allowed tables and read-only operations

If the prompt is unrelated, the system returns a domain rejection instead of fabricating an answer.

## LLM Configuration

The repo is wired to use Groq as the default hosted LLM provider.

Environment variables:

```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=your_groq_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
OPENAI_API_KEY=
OPENAI_BASE_URL=
```

Notes:

- Groq is integrated through the OpenAI-compatible Python client
- If no LLM key is configured, the backend still works in graph-backed mode

## Backend Structure

```text
backend/
  main.py                 FastAPI entrypoint wrapper
  app/
    main.py               FastAPI application factory
    query_engine.py       PostgreSQL pooling and query execution
    llm.py                Natural language to SQL translation
    guardrails.py         Public validation exports
    api/
      router.py
      v1/
        router.py
        endpoints/
          health.py
          graph.py
          query.py
    core/
      config.py
      database.py
    schemas/
      graph.py
      health.py
      query.py
    services/
      graph_store.py
      query_service.py
      ai/
        client.py
        guardrails.py
    db/
      base.py
      models.py
```

## Frontend Structure

```text
frontend/
  index.html
  package.json
  vite.config.js
  .env.example
  src/
    main.jsx
    App.jsx
    api.js
    QueryGraph.jsx
```

## Local Run

### Backend

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Render Deployment

Recommended backend deployment target: Render

### Build Command

If Render project root is the outer repo:

```bash
pip install -r erp-system/requirements.txt
```

### Start Command

If Render project root is the outer repo:

```bash
cd erp-system && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### Required Environment Variables

```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-20b
GROQ_API_KEY=your_groq_key
GROQ_BASE_URL=https://api.groq.com/openai/v1
```

### Important Render Notes

- commit `data/graph.json` and `data/graph_overview.json` to GitHub
- do not commit `.env`
- use `runtime.txt` to pin Python 3.11

## Vercel Deployment

Recommended frontend deployment target: Vercel

### Root Directory

`erp-system/frontend`

### Required Environment Variable

```env
VITE_API_BASE_URL=https://your-render-backend.onrender.com
```

Important:

- use only the base backend URL
- do not append `/api/v1`
- the frontend already appends `/api/v1/query` and `/api/v1/graph`

## Trade-offs

- The current graph reasoning layer is safer and more demo-reliable than a fully open-ended LLM planner, but less flexible
- SQL generation is available, but the graph path is the stronger default for this project
- The graph overview is intentionally bounded for frontend usability
- The real dataset graph is committed so the hosted app is reproducible without the original raw dataset
- Guardrails are intentionally conservative, which may reject some valid but unusual phrasing

## Why This System Exists

ERP failures are rarely isolated record problems. They are usually broken flows across multiple linked documents and entities. A useful debugging system therefore needs more than a chat interface. It needs explicit relationship modeling, bounded reasoning, and outputs that engineers can inspect under pressure.

This project is built to satisfy that need.
