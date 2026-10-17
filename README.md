# Enterprise HR Policy & Employee Support Agentic RAG Copilot

An end-to-end Forward Deployed Engineer (FDE) project that converts an Agentic RAG workflow into a deployable internal HR product: a **LangGraph + FastAPI** backend (Pinecone, Google Gemini, Tavily) and a **React + TypeScript** frontend that streams the agent's reasoning live, packaged with **Docker**.

## 1. Business Problem

### Customer
NovaRetail, a fictional 3,000-employee retail company.

### Problem
The HR team maintains many internal documents: leave policies, remote-work rules, payroll guidance, benefits information, onboarding procedures, conduct policies, and HR operations runbooks.

Employees still send repetitive HR questions because they do not know where the correct policy lives, keyword search returns too many documents, generic chatbots may invent policy details, internal documents may not cover current public regulations, and some questions require fresh external information.

### Example
An employee asks:

> “How many annual leave days do employees receive?”

The answer exists in the private company HR knowledge base, so the system should answer from internal policy without searching the public internet.

Another employee asks:

> “What are the latest public holiday rules in Bangladesh?”

The internal KB may not contain current public information. The system should recognize weak private evidence, use external search, grade the evidence, and clearly identify the answer as external information requiring HR validation.

### Business Goal
Build a secure HR Policy Copilot that:

1. Searches trusted private HR knowledge first.
2. Checks whether retrieved evidence is sufficient.
3. Uses web search only when private knowledge is insufficient.
4. Rewrites weak queries and retries.
5. Generates grounded answers.
6. Shows the LangGraph decision path for transparency and debugging.
7. Lets authorized HR staff add new company documents.

## 2. Why This Is an FDE Project

A Forward Deployed Engineer does more than build an LLM notebook. The FDE translates a customer problem into a usable product:

```text
Customer Problem
      ↓
Discovery & Requirements
      ↓
Solution Architecture
      ↓
Data / Knowledge Integration
      ↓
Agentic RAG Development
      ↓
API Development
      ↓
User Interface
      ↓
Security + Audit + Testing
      ↓
Deployment
      ↓
Observe + Improve
```

## 3. Simple Architecture

![System architecture](docs/architecture.png)

```text
Employee / HR User
        ↓
React + TypeScript Web UI
        ↓ POST /api/chat/{domain}/stream   (Server-Sent Events: one event per agent step)
FastAPI
        ↓
LangGraph Agentic RAG Controller  ←→  SQLite (conversation memory, audit)
        ↓
 ┌───────────────┬─────────────────┐
 ↓               ↓
Private HR KB    Tavily Web Search
Pinecone         (fallback only)
 └───────┬───────┘
         ↓
Gemini LLM
Grounded Answer
```

## 4. Agentic RAG Workflow

```text
Question
   ↓
[0] Contextualize (memory: follow-up → standalone question)
   ↓
[1] Route Question
   ├── Greeting / simple chat ─────────→ Direct Answer
   │
   └── HR / policy question
                ↓
[2] Retrieve from Private Pinecone KB
                ↓
[3] Grade Private Evidence
       ┌────────┴────────┐
       │                 │
     GOOD               WEAK
       │                 │
       ▼                 ▼
Generate from KB   [4] Tavily Web Search
       │                 ↓
       │          [5] Grade Web Evidence
       │            ┌────┴─────┐
       │            │          │
       │          GOOD        WEAK
       │            │          │
       │            ▼          ▼
       │      Generate Web  [6] Rewrite Query → Retry Private KB
       │            │          (max retry reached → Insufficient Evidence)
       └─────┬──────┘
             ↓
[7] Support check: is every claim grounded in the evidence?
       ├── fully supported ───────────────→ [8]
       ├── not yet revised ──→ Revise answer → re-check
       ├── partially supported after revision → [8]
       └── unsupported after revision ──→ Insufficient Evidence
             ↓
[8] Usefulness check: does it answer the question?
       ├── useful ──→ Answer (saved to conversation memory)
       └── not useful ──→ [6] Rewrite Query (or Insufficient Evidence)
```

## 5. Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent workflow | LangGraph | Stateful routing and conditional decisions |
| LLM | Google Gemini (`ChatGoogleGenerativeAI`) | Routing, grading, rewriting, answer generation |
| Embeddings | Gemini `gemini-embedding-2-preview` | Vector embeddings |
| Vector DB | Pinecone | Private enterprise HR knowledge base |
| External search | Tavily | Fallback when company HR KB is insufficient |
| API | FastAPI | REST endpoints + Server-Sent Events streaming |
| Memory & audit | SQLite + LangGraph `SqliteSaver` | Conversation memory, decision-path logging |
| Frontend | React 19 + TypeScript + Vite | Employee-facing single-page app |
| UI | Tailwind CSS + shadcn/ui (Base UI) | Accessible components, light/dark theme |
| Server state | TanStack Query + axios | Caching, invalidation, typed API client |
| Client state & routing | Zustand + React Router | Preferences; one URL per conversation |
| Validation | Zod | Runtime validation of every API response |
| Testing | Pytest · Vitest + Testing Library + MSW | Backend and frontend tests without network calls |
| Packaging | Docker + docker compose (nginx for the frontend) | Reproducible deployment |

## 6. Project Structure

Each business domain has its **own LangGraph workflow** and its **own Pinecone namespace**, built from shared, reusable nodes.

```text
Enterprise-HR-Policy-Agentic-RAG-Copilot/
├── app/                         Backend (FastAPI, API only)
│   ├── api/
│   │   ├── chat.py              POST /api/chat/{domain} and /stream (SSE)
│   │   ├── sessions.py          Conversation list and history
│   │   ├── ingest.py            Document upload, list, delete
│   │   ├── health.py            GET /api/health, GET /api/domains
│   │   └── errors.py            Provider failures → actionable 503/504 messages
│   ├── core/
│   │   ├── config.py            Settings loaded from .env
│   │   ├── llm.py               Gemini chat model (timeout, retries) + text helper
│   │   └── logging.py
│   ├── rag/
│   │   ├── common/              Shared building blocks
│   │   │   ├── nodes.py         Reusable node factories + edge conditions
│   │   │   ├── state.py         Agent state and structured outputs
│   │   │   ├── memory.py        SQLite checkpointer per conversation
│   │   │   └── vectorstore.py   Pinecone access per namespace
│   │   ├── hr/                  HR workflow
│   │   │   ├── graph.py
│   │   │   ├── prompts.py
│   │   │   └── ui.py            Labels, examples and colour shown by the frontend
│   │   └── registry.py          domain → workflow + namespace + UI settings
│   ├── services/                audit, conversations, documents, ingestion (SQLite + Pinecone)
│   └── main.py
├── frontend/                    React + TypeScript single-page app
│   ├── src/
│   │   ├── api/                 axios client, Zod schemas, SSE streaming
│   │   ├── hooks/               TanStack Query hooks, useChat (live stream)
│   │   ├── stores/              Zustand (theme, drawers)
│   │   ├── routes/              /:domain and /:domain/c/:threadId
│   │   ├── components/          chat, layout, documents, ui (shadcn/ui)
│   │   └── test/                MSW handlers and test setup
│   ├── Dockerfile               Node build → nginx
│   └── nginx.conf.template      Static files + /api reverse proxy (SSE-friendly)
├── data/documents/
│   ├── hr/                      Sample HR knowledge base
│   └── cloudops/                (coming next)
├── tests/                       Pytest suite (no network calls)
├── Dockerfile                   Backend image
├── docker-compose.yml           Backend + frontend
├── .env.example
├── ingest_sample_kb.py
├── requirements.txt / requirements-dev.txt
└── run.py
```

### Adding a new domain

1. Add documents to `data/documents/<domain>/`.
2. Create `app/rag/<domain>/prompts.py`, `graph.py` and `ui.py`, reusing the nodes in `app/rag/common/nodes.py`.
3. Register it in `app/rag/registry.py` with its own namespace. The frontend picks it up automatically (new tab).
4. Run `python ingest_sample_kb.py --domain <domain>`.

## 7. Setup

### Step 1 — Create and activate a virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS/Linux:

```bash
source venv/bin/activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Configure environment

Copy `.env.example` to `.env` and add your keys.

```env
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_INDEX_NAME=fde-hr-policy-rag
HR_NAMESPACE=company-hr-kb
GEMINI_MODEL=gemini-3.5-flash-lite
EMBEDDING_MODEL=gemini-embedding-2-preview
EMBEDDING_DIMENSION=768
ADMIN_API_KEY=change-me-in-production
APP_ENV=development
```

`PINECONE_NAMESPACE` is still accepted as an alias for `HR_NAMESPACE`. `EMBEDDING_DIMENSION` must match the existing Pinecone index: on a mismatch the app stops with an error instead of deleting the index.

### Step 4 — Load sample HR knowledge

```bash
python ingest_sample_kb.py --domain hr
```

### Step 5 — Run the application (two terminals)

Backend (API on port 8080, docs at `http://127.0.0.1:8080/docs`):

```bash
python run.py
```

Frontend (requires Node.js 20+):

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server forwards `/api` to the backend; set `API_PROXY_TARGET` in `frontend/.env` if the backend runs elsewhere (see `frontend/.env.example`).

### Step 6 — Run the tests

```bash
pip install -r requirements-dev.txt
pytest                      # backend: fake LLM, retriever and web search, no API keys needed

cd frontend
npm test                    # frontend: Vitest + Testing Library, API mocked with MSW
npm run typecheck
```

## Docker (deployment)

Two images, one per service:

| Image | Dockerfile | Contents |
|---|---|---|
| Backend | `Dockerfile` | FastAPI + LangGraph, non-root user, health check on `/api/health`, listens on `$PORT` (8080) |
| Frontend | `frontend/Dockerfile` | Multi-stage: Node builds the app, nginx serves it and proxies `/api` to `$API_UPSTREAM` with buffering off for streaming |

```bash
docker compose up --build
# → app on http://localhost:3000, API docs on http://localhost:8080/docs

docker compose run --rm backend python ingest_sample_kb.py --domain hr   # index the sample documents
```

SQLite data lives in the `backend-data` volume. Both images honour the `PORT` variable, so they can also run as separate web services on a container host such as Render.

## API

| Method | Route | Description |
|---|---|---|
| GET | `/api/health` | Service status |
| GET | `/api/domains` | Available domains and their UI settings |
| POST | `/api/chat/{domain}` | Ask a question (`{"question": "...", "thread_id": "..."}`) |
| POST | `/api/chat/{domain}/stream` | Same, as Server-Sent Events: `start`, one `step` per trace line, then `result` or `error` |
| GET | `/api/sessions/{domain}` | Previous conversations of a domain (title, turns, last update) |
| GET | `/api/sessions/{domain}/{thread_id}` | Conversation history |
| DELETE | `/api/sessions/{domain}/{thread_id}` | Forget a conversation |
| POST | `/api/ingest/{domain}` | Upload a document (header `X-Admin-Key`); re-uploading the same file replaces it |
| GET | `/api/documents/{domain}` | Documents indexed through the app |
| DELETE | `/api/documents/{domain}/{filename}` | Remove a document from the knowledge base (header `X-Admin-Key`) |

`POST /api/chat` and `POST /api/ingest` remain as aliases for the `hr` domain.

## Conversation Memory

Each conversation has a `thread_id`, visible in the URL (`/hr/c/<thread_id>`) and generated by the API if omitted. LangGraph's SQLite checkpointer stores the conversation in `data/memory.db`, and a `contextualize` node rewrites follow-ups such as *"And for sick leave?"* into standalone questions before retrieval. `MEMORY_TURNS` controls how many previous turns are used.

## Credits

Conversation memory is adapted from [CloudOps Sentinel Copilot](https://github.com/entbappy/CloudOps-Sentinel-Copilot) (MIT License). See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## 8. Classroom Demo Scenarios

### Demo A — Private KB Success
Ask: **How many annual leave days do employees receive?**

Expected path:

```text
Router → KB
Private KB Retrieval
KB Grade → GOOD
Generate from Private KB
```

### Demo B — Company Policy Question
Ask: **How many days per week can I work remotely?**

Expected result: answer from the internal HR handbook, without web search.

### Demo C — External / Current Information
Ask: **What are the latest public holiday rules in Bangladesh?**

Expected path when internal HR documents are insufficient:

```text
Router → KB
Private KB Retrieval
KB Grade → WEAK
Tavily Search
Web Grade → GOOD
Web Answer
```

### Demo D — Weak Query Rewrite
Ask an ambiguous HR question such as: **What happens if mine is wrong?**

If neither private nor web evidence is sufficient, the workflow can rewrite the query, retry the KB, and eventually stop with insufficient evidence rather than hallucinating.

## 9. What Changed From the IT Support Reference

The application structure, graph topology, API shape, retrieval logic, ingestion layer, audit layer, Docker setup, and frontend behavior remain the same. Only domain-specific elements were changed: HR prompts, HR configuration names, UI wording, example questions, sample documents, and documentation.