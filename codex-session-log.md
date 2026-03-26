# Codex Session Log

## Metadata

- Project: ERP Workflow Debugging System
- Role context used across session: backend engineer, data engineer, AI engineer, frontend engineer, product engineer, senior engineer, forward deployed engineer
- Workspace root: `C:\Users\tusha\OneDrive\Documents\Task-FDE-Dodge-1`
- App root: `C:\Users\tusha\OneDrive\Documents\Task-FDE-Dodge-1\erp-system`
- Date range: 2026-03-23 to 2026-03-26
- Primary tools used: Codex desktop, local shell, FastAPI, React, Cytoscape, Groq-compatible OpenAI client, Render, Vercel

## Session Goal

Build a graph-based ERP workflow exploration system with:

- FastAPI backend
- PostgreSQL integration
- graph modeling over SAP O2C data
- natural language query interface
- guardrails
- React frontend
- graph visualization
- deployment-ready structure

## Chronological Log

### 1. Backend scaffold and project structure

User request:
- Set up a FastAPI backend with PostgreSQL integration
- keep it modular
- output folder structure and dependencies

Work completed:
- scaffolded modular FastAPI backend
- added config, database, API router, schemas, and AI service structure
- added `pyproject.toml`, `requirements.txt`, `.env.example`, and `README.md`

Key files created/updated:
- `erp-system/backend/app/main.py`
- `erp-system/backend/app/core/config.py`
- `erp-system/backend/app/core/database.py`
- `erp-system/backend/app/api/...`
- `erp-system/pyproject.toml`
- `erp-system/requirements.txt`

### 2. PostgreSQL query execution

User request:
- write PostgreSQL connection code in Python using `psycopg2`
- reusable function for executing SQL
- return JSON-friendly results

Work completed:
- added reusable `execute_select_query()` helper
- returned rows as list of dictionaries
- restricted execution to `SELECT`

Key file:
- `erp-system/backend/db.py` initially, later refactored into app-layer runtime modules

### 3. Connection pooling

User request:
- refactor PostgreSQL connection to use pooling

Work completed:
- replaced per-query connection creation with `psycopg2.pool.ThreadedConnectionPool`
- added safe connection release and pool close behavior

Key outcomes:
- better performance model
- more production-oriented DB access

### 4. ERP schema design

User request:
- design relational schema for ERP workflow

Work completed:
- provided SQL `CREATE TABLE` statements for:
  - customers
  - orders
  - deliveries
  - invoices
  - payments

Purpose:
- establish clear lifecycle dependency model:
  - orders -> deliveries -> invoices -> payments

### 5. Natural language to SQL layer

User request:
- build Python function using OpenAI API to convert natural language to SQL
- prevent hallucination
- only return SQL

Work completed:
- implemented constrained NL-to-SQL function
- added SQL validation for:
  - read-only queries
  - allowed tables
  - allowed join patterns
- later moved this code into backend module

Key file:
- `erp-system/backend/app/llm.py`

### 6. Guardrails

User request:
- add guardrails so only ERP-related queries are accepted

Work completed:
- implemented simple keyword-based ERP domain validator
- rejected unrelated prompts before LLM/query execution

Key files:
- `erp-system/backend/app/services/ai/guardrails.py`
- `erp-system/backend/app/guardrails.py`

### 7. Query endpoint

User request:
- build FastAPI endpoint for query system
- input: natural language
- output: SQL + data

Work completed:
- added `POST /api/v1/query`
- added request/response schemas
- added error handling

Key files:
- `erp-system/backend/app/api/v1/endpoints/query.py`
- `erp-system/backend/app/schemas/query.py`

### 8. Backend runtime/debug stabilization

Major issues encountered:
- missing module imports
- broken package paths
- `backend` import failures under Uvicorn
- file/package naming conflicts (`backend.app.db`)
- pydantic version mismatch
- root endpoint returning 404

Fixes applied:
- normalized backend imports to relative imports
- added root-level launch shims
- created `main.py` wrappers for Uvicorn compatibility
- resolved `db.py` vs `db/` package collision by moving query runtime to `query_engine.py`
- added root `/` API status endpoint
- aligned pydantic/FastAPI stack for deployment

Key files:
- `main.py`
- `erp-system/main.py`
- `erp-system/backend/main.py`
- `erp-system/backend/app/query_engine.py`
- `erp-system/backend/app/main.py`

### 9. Frontend creation

User request:
- create React UI for ERP workflow query system
- input box, submit, SQL output, JSON result

Work completed:
- built initial React UI using functional components
- added fetch integration to backend
- later improved styling, spacing, loading state, and error handling

Key files:
- `erp-system/frontend/src/App.jsx`
- `erp-system/frontend/src/api.js`

### 10. Graph visualization

User request:
- visualize query results as graph using Cytoscape.js
- improve readability

Initial approach:
- graph view of returned rows

Later refinement:
- moved to actual entity graph visualization using node/edge payloads
- improved layout and node labeling

Key file:
- `erp-system/frontend/src/QueryGraph.jsx`

### 11. README and architecture writing

User request:
- write professional README
- emphasize architecture, design decisions, guardrails, trade-offs, and production thinking

Work completed:
- rewrote README multiple times
- aligned docs with:
  - reliability model
  - LLM control strategy
  - debugging workflows
  - graph modeling
  - deployment story

Key file:
- `erp-system/README.md`

### 12. Assignment alignment review

User provided the full assignment overview.

Gap analysis performed:
- current build was only a partial SQL/query prototype
- assignment required a true context graph system
- highlighted missing pieces:
  - dataset ingestion
  - graph construction
  - graph endpoints
  - graph exploration UI
  - grounded query answers

Decision:
- reorient project around graph-first architecture

### 13. Real dataset integration

User provided dataset path:
- `C:\Users\tusha\Downloads\sap-order-to-cash-dataset\sap-o2c-data`

Dataset inspection covered:
- sales order headers/items
- delivery headers/items
- billing document headers/items
- journal entries
- payments
- business partners
- addresses
- products
- product descriptions
- plants

Key modeling decisions:
- nodes:
  - customer
  - address
  - order
  - product
  - plant
  - delivery
  - invoice
  - journal_entry
  - payment
- edges:
  - customer -> order (`placed`)
  - customer -> address (`located_at`)
  - order -> product (`contains`)
  - order -> plant (`sourced_from`)
  - order -> delivery (`fulfilled_by`)
  - delivery -> plant (`ships_from`)
  - delivery -> invoice (`billed_by`)
  - invoice -> journal_entry (`posted_to`)
  - invoice -> payment (`settled_by`)

### 14. Graph ingestion pipeline

Work completed:
- created ingestion script to transform SAP JSONL parts into graph JSON
- generated both:
  - full graph
  - overview graph

Key file:
- `erp-system/scripts/build_graph_from_sap.py`

Generated artifacts:
- `erp-system/data/graph.json`
- `erp-system/data/graph_overview.json`
- retained `erp-system/data/sample_graph.json` as fallback

Generation result:
- full graph nodes: 724
- full graph edges: 993

### 15. Graph services and APIs

Work completed:
- created graph schema models
- built graph store service
- added graph endpoints

Key files:
- `erp-system/backend/app/schemas/graph.py`
- `erp-system/backend/app/services/graph_store.py`
- `erp-system/backend/app/api/v1/endpoints/graph.py`

Available endpoints:
- `GET /api/v1/graph`
- `GET /api/v1/graph/search`
- `GET /api/v1/graph/nodes/{node_id}`

### 16. Graph-backed query reasoning

Work completed:
- added query service for graph-backed answers
- supported patterns such as:
  - highest billing-document count by product
  - incomplete/broken flows
  - trace document flow
  - invoice payment status
  - graph search fallback

Key file:
- `erp-system/backend/app/services/query_service.py`

Behavior:
- if LLM/SQL available, system can use it
- otherwise falls back to graph-backed dataset reasoning

### 17. Groq integration

User request:
- integrate Groq since free-tier access is available

Work completed:
- switched provider config to support Groq first
- used OpenAI-compatible Groq endpoint
- made LLM provider configurable by env vars

Key files:
- `erp-system/backend/app/core/config.py`
- `erp-system/backend/app/services/ai/client.py`
- `erp-system/backend/app/llm.py`
- `erp-system/.env.example`

Relevant env vars:
- `LLM_PROVIDER`
- `LLM_MODEL`
- `GROQ_API_KEY`
- `GROQ_BASE_URL`
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`

### 18. Deployment support

Backend deployment:
- targeted Render
- added runtime version pins
- fixed FastAPI/pydantic deployment mismatch

Frontend deployment:
- targeted Vercel
- added Vite app scaffold

Key files:
- `runtime.txt`
- `erp-system/runtime.txt`
- `erp-system/frontend/package.json`
- `erp-system/frontend/vite.config.js`
- `erp-system/frontend/index.html`
- `erp-system/frontend/src/main.jsx`

### 19. Deployment issues debugged

Render issues:
- missing module imports
- `backend` package path resolution
- pydantic mismatch with deployed FastAPI

Fixes:
- cleaned package imports
- added launch shims
- pinned compatible Python/runtime/dependency versions

Vercel issues:
- `vite` permission denied
- caused by committed `node_modules`

Resolution guidance:
- remove `frontend/node_modules` from repo
- keep only `package.json` and lockfile

### 20. Product/demo QA

Observed issue:
- valid query `Show all invoices with their payment status.` was rejected or returned not found in some flows

Fixes:
- broadened ERP keyword guardrails
- added invoice/payment-status query handler
- clarified backend/frontend URL alignment guidance

## Important Technical Decisions

### Graph-first instead of SQL-first

Reason:
- assignment is fundamentally about fragmented business relationships
- graph modeling makes lifecycle inspection explicit
- graph answers are safer fallback when SQL/LLM path is unavailable

### LLM as constrained translation layer

Reason:
- avoid hallucination
- keep answers inspectable
- allow graceful fallback to graph-backed reasoning

### Generated graph artifacts committed to repo

Reason:
- hosted demo should not depend on local dataset path
- makes Render/Vercel deployment reproducible

## Final Repo Components Produced During Session

- backend API
- graph ingestion script
- graph data artifacts
- graph service/query service
- React frontend
- Cytoscape visualization
- README
- Groq integration
- deployment guidance
- launch shims

## Files Most Relevant To Submission

- `main.py`
- `erp-system/README.md`
- `erp-system/data/graph.json`
- `erp-system/data/graph_overview.json`
- `erp-system/scripts/build_graph_from_sap.py`
- `erp-system/backend/app/services/graph_store.py`
- `erp-system/backend/app/services/query_service.py`
- `erp-system/backend/app/api/v1/endpoints/query.py`
- `erp-system/backend/app/api/v1/endpoints/graph.py`
- `erp-system/frontend/src/App.jsx`
- `erp-system/frontend/src/QueryGraph.jsx`

## Notes For Reviewers

- The system evolved from a SQL-oriented prototype into a graph-based ERP debugging application during this session.
- The final architecture intentionally supports both graph-backed reasoning and optional LLM-assisted SQL generation.
- The deployed/demo path should use the committed graph artifacts rather than relying on the raw local SAP dataset.
