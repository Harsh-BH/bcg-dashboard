# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HR Headcount Dashboard for BCG — a **Next.js 16 + FastAPI** application. The Python data-processing logic (originally from a monolithic Streamlit app) lives in a FastAPI backend; the frontend is a React 19 single-page dashboard deployed on Vercel. The app includes **AI-powered analytics** (chat, auto-commentary, anomaly detection) and **PDF report generation**.

---

## Repository Layout

```
bcg-dashboard/
├── hr_dashboard/         ← Original Streamlit app (reference for Python logic)
│   ├── app.py            ← 3,600-line monolith — DO NOT delete; mine for logic
│   └── HRMS_FOLDER/      ← Local HRMS_YYYY_MM_DD.xlsx snapshots
├── frontend/             ← Next.js 16 app (Vercel)
└── backend/              ← FastAPI app (Railway)
```

---

## Frontend (Next.js 16)

### Setup & Dev

```bash
cd frontend
npm install
npm run dev        # localhost:3000
npm run build
```

### Key commands (shadcn)

```bash
npx shadcn@latest add <component>
```

### Stack

- **Next.js 16 App Router** (Turbopack) + **React 19**
- **shadcn/ui v4** (`@base-ui/react` primitives) + **Tailwind CSS v4** + `tw-animate-css`
- **Recharts** — area/line charts with gradient fills
- **TanStack Table v8** — sortable, filterable, cell-click drill-down tables
- **Zustand** — global state (months, drill-down, AI chat/commentary/anomalies)
- **React Query (@tanstack/react-query)** — `useMutation` for POST /process, `staleTime: Infinity`
- **OpenAI SDK v6** — server-side API routes for GPT-4o (chat, commentary, anomalies)
- **@react-pdf/renderer** — client-side PDF report generation
- **html-to-image** — chart snapshot for PDF embedding
- **SheetJS (xlsx)** — client-side Excel export (single + multi-sheet) and HRMS header validation
- **react-markdown + remark-gfm** — rendering AI chat and commentary output
- **Axios** — HTTP client for backend API
- **Zod v4** — schema validation (peer dep for openai/shadcn/MCP SDK)
- **Font**: DM Sans (Google Fonts)

### Project structure

```
frontend/
├── app/
│   ├── layout.tsx              # Root layout, DM Sans, QueryProvider
│   ├── page.tsx                # Single-page dashboard shell (tabs, AI bar, loading)
│   ├── globals.css             # Tailwind v4 + shadcn theme tokens + loading-bar keyframes
│   └── api/ai/
│       ├── chat/route.ts       # POST — GPT-4o streaming chat (SSE)
│       ├── commentary/route.ts # POST — GPT-4o streaming executive commentary (SSE)
│       └── anomalies/route.ts  # POST — GPT-4o anomaly detection (tool call → JSON)
├── components/
│   ├── layout/
│   │   └── Sidebar.tsx         # Multi-file upload, optional files, payroll dates, Generate
│   ├── tabs/
│   │   ├── OverallView.tsx     # Trend chart + MoM overview + pair drill-down
│   │   ├── HrmsWalk.tsx        # Reconciliation table + base/compare selects
│   │   ├── SpanMovement.tsx    # Unknown grades, cluster trend, service line tables
│   │   └── SpartanChecks.tsx   # Per-snapshot Spartan + payroll metrics/tables
│   ├── charts/
│   │   └── HeadcountTrendChart.tsx  # Recharts area chart + metric selector
│   ├── tables/
│   │   ├── DrillDownTable.tsx  # TanStack Table + cell-click → people list + Excel export
│   │   └── HierarchyTable.tsx  # Styled grand total / delivery / support rows
│   ├── ai/
│   │   ├── ChatDrawer.tsx      # Slide-over chat panel, markdown, suggested prompts
│   │   ├── CommentaryModal.tsx # Dialog for streaming commentary, copy, .md export
│   │   ├── AnomalyAlertList.tsx # Per-tab anomaly cards with severity badges
│   │   └── ReportDocument.tsx  # @react-pdf/renderer PDF layout (overview + commentary + anomalies + chart)
│   ├── providers/
│   │   └── QueryProvider.tsx   # TanStack QueryClient (staleTime: Infinity, retry: 1)
│   └── ui/                     # shadcn generated components (alert, badge, button, card, dialog, etc.)
├── hooks/
│   ├── useDashboardData.ts     # useMutation → processFiles; auto-triggers anomaly scan on success
│   ├── useChat.ts              # Streams POST /api/ai/chat, updates Zustand messages
│   ├── useCommentary.ts        # Streams POST /api/ai/commentary into store
│   └── useReportGeneration.ts  # Orchestrates commentary + anomalies → PDF blob download
├── lib/
│   ├── api.ts                  # Axios instance + processFiles (multipart POST to backend)
│   ├── types.ts                # Shared TS types mirroring backend JSON + AI types
│   ├── utils.ts                # cn(), fmtPct/fmtNum, downloadExcel/downloadMultiSheetExcel
│   ├── ai-context.ts           # buildDashboardContext — text summary of data for LLM prompts
│   ├── claude-stream.ts        # Browser SSE reader for AI route responses
│   └── hrms-validator.ts       # Client-side XLSX header validation (required/recommended cols, fuzzy match)
└── store/
    └── dashboardStore.ts       # Zustand: data, loading, month pairs, drill, span, AI (chat/commentary/anomalies)
```

### Design tokens

```css
:root {
  --sidebar-bg:  gradient slate-800 → slate-900;
  --card:        white, rounded-2xl, shadow-sm, border-slate-100;
  --primary:     #3b82f6 / #2563eb;
  --foreground:  #0f172a;
}
```

Active tab: blue gradient pill. Drill-down row: `bg-blue-50 border-l-2 border-blue-500`.

---

## AI Features

### Architecture

AI runs through **Next.js API routes** (server-side, `OPENAI_API_KEY` env var) — not through the Python backend. The frontend streams responses via SSE.

### Chat (`/api/ai/chat`)

- Slide-over `ChatDrawer` with markdown rendering, streaming dots, suggested prompts
- System prompt: BCG HR analytics expert; receives `dashboardContext` (built from processed data)
- Stores messages in Zustand; `useChat` hook manages streaming

### Commentary (`/api/ai/commentary`)

- "Generate Insights" button triggers `useCommentary` hook
- Streams executive MoM commentary (Executive Summary, Headcount Movement, Bucket Analysis, Anomalies & Watch Items)
- `CommentaryModal` with copy-to-clipboard and `.md` file download

### Anomaly Detection (`/api/ai/anomalies`)

- Auto-triggered after data processing completes (`useDashboardData` → on success)
- Uses OpenAI **tool calling** (`report_anomalies` function) for structured JSON output
- `AnomalyAlertList` renders per-tab anomaly cards with severity badges (high/medium/low)
- Tab badges show anomaly counts; floating chat FAB shows total count

### PDF Report (`useReportGeneration`)

- Orchestrates: ensure commentary exists → ensure anomalies exist → capture chart as PNG → generate PDF
- `ReportDocument` uses `@react-pdf/renderer` for layout: header, overview table, commentary, anomalies, chart image
- Downloads as `headcount-report-YYYY-MM-DD.pdf`

---

## Backend (FastAPI)

### Setup & Dev

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
python -m uvicorn main:app --reload   # localhost:8000
```

All modules use **absolute imports** (`from logic.X import ...`) so uvicorn must be run from inside `backend/`.

### Stack

- **FastAPI** — two endpoints: `POST /api/process`, `GET /api/drill`
- **pandas + openpyxl + python-calamine + numpy** — data processing
- **Pydantic v2** — request/response schemas
- **In-memory session cache** — keyed by MD5 of file bytes; max 5 sessions; stores DataFrames for drill-down
- CORS: `ALLOWED_ORIGINS` env var (defaults to `*`)

### Module layout

All Python logic originated from `hr_dashboard/app.py` — do not rewrite logic from scratch:

| Module | Purpose |
|---|---|
| `logic/constants.py` | HRMS filename regex, bucket strings, span grade bands, TL designation phrases, service-line process/CC sets, month-specific overrides |
| `logic/normalization.py` | Column aliasing for HRMS, Spartan, payroll, and span data |
| `logic/bucketing.py` | `classify_bucket_type1` / `type2` (→ `BUCKET`), `detect_file_type`, `normalize_support_buckets` |
| `logic/snapshot.py` | `load_snapshot`, `prepare_hr_snapshot` (Excel read, HR cleaning, bucket assignment, counts) |
| `logic/table_builders.py` | `build_hier_table`, `build_reconciliation_table`, `build_reconciliation_salary_table`, `build_metric_trend` |
| `logic/span.py` | Conneqt masking, unknown grades, IC/TL/M1+ classification (graph + designation), cluster mapping, trend by cluster, service-line wide tables |
| `logic/spartan.py` | Spartan D2 processing, payroll reconciliation, `build_spartan_checks`, `build_payroll_checks` |
| `logic/utils.py` | `keyify`, `to_id_string`, Excel I/O, salary aggregation, ID normalization |

### API contract

#### `POST /api/process` — `multipart/form-data`

Request fields: `hrms_files[]` (≥2 XLSX), `spartan_file` (optional), `payroll_file` (optional), `conneqt_mapping_file` (optional), `payroll_start` (YYYY-MM-DD), `payroll_end` (YYYY-MM-DD).

Response JSON shape:
```json
{
  "session_id": "md5-hash",
  "snapshots": [{ "label": "...", "month_key": [2026, 3, 14] }],
  "trend": { "labels": [], "total": [], "delivery": [], "support": [], "cxo": [] },
  "overview_table": [],
  "pair_tables": { "<label>": { "hier_table": [], "people": {} } },
  "reconciliation_tables": {},
  "span": {},
  "spartan_checks": {},
  "validation_warnings": []
}
```

#### `GET /api/drill` — query params

`session_id`, `snapshot_label`, `category`, `id_set` (`"all"` or comma-separated employee IDs). Returns up to 5,000 people rows from the in-memory session cache.

### Processing pipeline

1. **Validate** uploads (≥2 HRMS files)
2. **Load** HRMS snapshots in parallel → normalize, detect type1/type2, bucket, count
3. **Cache** session (MD5 key, max 5) — stores DataFrames + reconciliation subsets for drill
4. **Optional** Spartan/payroll parsing
5. **Build** metric trend, all-pair overview, hierarchical tables, reconciliation (counts + salary)
6. **Span** analysis: unknown grades, IC/TL/M1+ classification, cluster mapping, service-line tables
7. **Spartan checks** per snapshot pair + payroll block
8. **Return** JSON response

### File validation

Filename regex: `^HRMS_(\d{4})_(0[1-9]|1[0-2])_(0[1-9]|[12]\d|3[01])\.xlsx$`
Minimum 2 HRMS files required — validated in FastAPI, surfaced as `<Alert destructive>` on frontend.

---

## Deployment

### Frontend → Vercel

```bash
cd frontend && vercel --prod
```

Env vars: `NEXT_PUBLIC_API_URL=https://<railway-app>.railway.app`, `OPENAI_API_KEY`.

### Backend → Railway

```toml
# railway.toml
[build]
builder = "DOCKERFILE"
[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

Dockerfile: `python:3.11-slim`, env var `ALLOWED_ORIGINS` → set to Vercel URL.

---

## Domain Concepts

**Buckets**: `Conneqt Business Solution`, `Alldigi`, `Tech & Digital`, `CXO`, `Support Functions - *`. Classification via `classify_bucket_type1()` / `classify_bucket_type2()`.

**Role Classification (IC / TL / M1+)**: `span_classify_ic_tl_m1()` — based on grade codes (`A1.x`, `A2.x`, `A3`, `A4`, `PT`, `AT`), reportee counts, designation matching, and reporting-tree graph traversal.

**Service Lines**: Derived from the `PROCESS` column via `span_service_line_keys_series()` — encodes hierarchy using constants-defined process/CC sets with month-specific overrides.

**Reconciliation**: `build_reconciliation_table()` tracks joins, exits (Spartan + BAU), transfers between two HRMS snapshots. Optional salary table (`build_reconciliation_salary_table`) when `OTC PA` column is present.

**Conneqt Cluster Mapping**: Optional Excel upload maps cost codes to clusters for span analysis aggregation.

---

## Tab Specs

| Tab | Key Components |
|---|---|
| 1 — Overall View | `HeadcountTrendChart` (Recharts AreaChart, metric selector) + MoM overview + pair drill-down + Excel export |
| 2 — HRMS Walk | Reconciliation table with base/compare selects + `DrillDownTable` with clickable count columns + people list Excel export |
| 3 — Span Movement | Unknown grades, cluster trend (IC/TL/M1+), service-line wide tables (multi-sheet Excel), single-snapshot view, TL phrase collapsible |
| 4 — Spartan/HRMS/Payroll | Per-snapshot metric cards + D2 cross-check table + payroll flagged table + `<Alert>` for edge cases |

---

## Export Capabilities

| Format | Feature |
|---|---|
| Excel (single sheet) | MoM overview, drill-down tables, span exports, Spartan/payroll flagged lists |
| Excel (multi-sheet) | Span service-line workbook (3 sheets) |
| Markdown | Commentary modal → `.md` file download |
| PDF | Full report: overview table + AI commentary + anomalies + chart image |
| People drill-down | `DrillDownTable` exports `people_<filename>.xlsx` |

---

## Loading & UX

- **Full-page loading screen**: cycling status messages, animated dots, spinner ring, indeterminate progress bar (`loading-bar` CSS keyframes)
- **Per-action spinners**: Generate Insights, Export Report, Generate Dashboard buttons
- **Empty state**: prompt card when no data has been processed yet
- **Animations**: `tw-animate-css` for tab transitions, sidebar list items, drill panel, chat drawer

---

## Roadmap (future phases)

- **Auth**: NextAuth.js — role-based access
- **Persistent storage**: Supabase — no re-upload on refresh, session history
- **Dark mode**: Tailwind `dark:` variant (shadcn already supports it)
- **Enhanced AI**: conversation history persistence, custom prompt templates, multi-model support
- **Notifications**: scheduled anomaly alerts, email digests
- **Collaboration**: shared dashboard sessions, annotation/comments on data points
