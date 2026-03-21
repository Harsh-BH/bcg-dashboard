# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HR Headcount Dashboard for BCG — being migrated from a monolithic Streamlit app to **Next.js 14 + FastAPI**. The existing Python data-processing logic is kept intact in a FastAPI backend; the frontend becomes a React app deployed on Vercel.

---

## Repository Layout (post-migration)

```
bcg-dashboard/
├── hr_dashboard/         ← Original Streamlit app (source of truth for Python logic)
│   ├── app.py            ← 3,600-line monolith — DO NOT delete; mine for logic
│   └── HRMS_FOLDER/      ← Local HRMS_YYYY_MM_DD.xlsx snapshots
├── frontend/             ← Next.js 14 app (Vercel)
└── backend/              ← FastAPI app (Railway)
```

---

## Frontend (Next.js 14)

### Setup & Dev

```bash
cd frontend
npm install
npm run dev        # localhost:3000
npm run build
npm run lint
```

### Key commands (shadcn)

```bash
npx shadcn@latest add <component>
```

### Stack

- **Next.js 14 App Router** — file-based routing, RSC
- **shadcn/ui + Tailwind CSS v3** — component library
- **Recharts** — line/bar charts
- **TanStack Table v8** — sortable, filterable, cell-click tables
- **Zustand** — global state (selected months, drill-down cell, uploaded file list)
- **React Query (@tanstack/react-query)** — POST /process, staleTime: Infinity
- **react-dropzone** — multi-file HRMS upload + single Spartan/Payroll upload
- **SheetJS (xlsx)** — client-side Excel export on every table
- **Axios** — HTTP client
- **React Hook Form + Zod** — sidebar form validation
- **Font**: DM Sans (Google Fonts) — same as Streamlit app

### Project structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout, DM Sans, theme
│   ├── page.tsx            # Dashboard shell
│   └── globals.css         # Tailwind base + CSS variables
├── components/
│   ├── layout/
│   │   ├── Sidebar.tsx     # Uploads, payroll dates, Generate button
│   │   └── Header.tsx
│   ├── tabs/
│   │   ├── OverallView.tsx
│   │   ├── HrmsWalk.tsx
│   │   ├── SpanMovement.tsx
│   │   └── SpartanChecks.tsx
│   ├── charts/
│   │   └── HeadcountTrendChart.tsx
│   ├── tables/
│   │   ├── DrillDownTable.tsx    # TanStack Table + cell-click → people list
│   │   ├── HierarchyTable.tsx    # Styled grand total / delivery rows
│   │   └── OverviewTable.tsx
│   └── ui/                       # shadcn generated components
├── hooks/
│   ├── useDashboardData.ts   # React Query: POST /process
│   └── useFileUpload.ts      # Dropzone + multi-file state
├── lib/
│   ├── api.ts                # Axios instance + typed endpoints
│   ├── types.ts              # Shared TS types mirroring backend JSON
│   └── utils.ts              # shadcn cn() + formatters
└── store/
    └── dashboardStore.ts     # Zustand: selectedMonths, drillCell, peopleList
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

## Backend (FastAPI)

### Setup & Dev

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --app-dir .   # localhost:8000
# Or equivalently:
python -m uvicorn main:app --reload
```

All modules use **absolute imports** (`from logic.X import ...`) so uvicorn must be run from inside `backend/`.

### Stack

- **FastAPI** — single endpoint `POST /process`
- **pandas + openpyxl + numpy** — same as Streamlit app
- **Pydantic v2** — request/response schemas
- CORS: allow only the Vercel frontend origin (set via `ALLOWED_ORIGINS` env var)

### Module layout

All Python logic is **copy-pasted from `hr_dashboard/app.py`** into these modules — do not rewrite logic from scratch:

| Module | Functions from app.py |
|---|---|
| `logic/utils.py` | `keyify`, `to_id_string`, `clean_text_series`, `df_to_excel_bytes`, `ensure_cols` |
| `logic/normalization.py` | `normalize_hr_cols`, `normalize_spartan_cols`, `normalize_payroll_cols`, `normalize_span_hrms_cols` |
| `logic/bucketing.py` | `classify_bucket_type1`, `classify_bucket_type2`, `detect_file_type`, `normalize_support_buckets` |
| `logic/snapshot.py` | `prepare_hr_snapshot`, `load_snapshot_from_path`, `scan_hr_folder` |
| `logic/table_builders.py` | `build_hier_table`, `build_reconciliation_table`, `make_trend_df`, `make_trend_chart` |
| `logic/span.py` | All `span_*` functions |
| `logic/spartan.py` | Tab 4 Spartan + Payroll cross-check logic |

**When migrating**: replace `st.cache_data` with an in-memory dict keyed on file hash; replace `st.error/st.stop()` with `raise ValueError(...)` or FastAPI `HTTPException`.

### API contract

`POST /process` — `multipart/form-data`

Request fields: `hrms_files[]` (multiple XLSX), `spartan_file` (optional), `payroll_file` (optional), `payroll_start` (YYYY-MM-DD), `payroll_end` (YYYY-MM-DD).

Response JSON shape:
```json
{
  "snapshots": [{ "label": "...", "month_key": [2026, 3, 14] }],
  "trend": { "labels": [], "total": [], "delivery": [], "support": [], "cxo": [] },
  "overview_table": [],
  "pair_tables": { "<label>": { "hier_table": [], "people": {} } },
  "reconciliation_tables": {},
  "span_tables": {},
  "spartan_checks": {},
  "validation_warnings": []
}
```

### File validation

Filename regex (unchanged from Streamlit): `^HRMS_(\d{4})_(0[1-9]|1[0-2])_(0[1-9]|[12]\d|3[01])\.xlsx$`
Minimum 2 HRMS files required — validate in FastAPI, surface as shadcn `<Alert destructive>` on frontend.

---

## Deployment

### Frontend → Vercel

```bash
cd frontend && vercel --prod
# Env var: NEXT_PUBLIC_API_URL=https://<railway-app>.railway.app
```

### Backend → Railway

```toml
# railway.toml
[build]
builder = "DOCKERFILE"
[deploy]
startCommand = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

`ALLOWED_ORIGINS` env var → set to Vercel URL.

---

## Domain Concepts (unchanged from Streamlit)

**Buckets**: `Conneqt Business Solution`, `Alldigi`, `Tech & Digital`, `CXO`, `Support Functions - *`. Classification via `classify_bucket_type1()` / `classify_bucket_type2()`.

**Role Classification (IC / TL / M1+)**: `span_classify_ic_tl_m1()` — based on grade codes (`A1.x`, `A2.x`, `A3`, `A4`, `PT`, `AT`), reportee counts, and designation matching.

**Service Lines**: Derived from the `PROCESS` column via `span_service_line_keys_series()` — encodes hierarchy, careful parsing required.

**Reconciliation**: `build_reconciliation_table()` tracks joins, exits, transfers between two HRMS snapshots.

---

## Tab Specs

| Tab | Key Components |
|---|---|
| 1 — Overall View | `HeadcountTrendChart` (Recharts LineChart) + `OverviewTable` + `DrillDownTable` + SheetJS download |
| 2 — HRMS Walk | `DrillDownTable` with 5 clickable count columns + styled summary table + animated slide-down people list |
| 3 — Span Movement | MoM span table + single-snapshot view + cluster summary + TL phrase collapsible |
| 4 — Spartan/HRMS/Payroll | Metric cards (`<Card>`) + D2 cross-check table + Payroll flagged table + `<Alert>` for edge cases |

---

## Phase 2 (out of scope now)

- Auth: NextAuth.js
- Persistent storage: Supabase (no re-upload on refresh)
- Dark mode: Tailwind `dark:` (shadcn already supports it)
- PDF export: react-pdf
