import io
from datetime import date, datetime
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from logic.constants import HR_FILE_RE
from logic.snapshot import (
    load_snapshot,
    prepare_hr_snapshot,
    validate_hrms_filename,
)
from logic.utils import read_excel_best_sheet, format_snapshot_date
from logic.normalization import normalize_hr_cols
from logic.table_builders import (
    build_hier_table,
    build_metric_trend,
    build_reconciliation_table,
    counts_from_ids,
    expand_bucket_selection,
    people_for_ids_and_buckets,
)
from logic.span import (
    span_prepare_and_detect_unknown,
    span_prepare_and_detect_unknown_all_business_units,
    span_classify_ic_tl_m1,
    span_trend_ic_tl_by_cluster,
    span_attach_cluster_and_summarize,
    span_service_line_wide_table,
    span_service_line_span_and_role_counts,
    load_conneqt_cluster_mapping,
    _span_normalize_bu_value,
)
from logic.spartan import (
    process_spartan_file,
    process_payroll_file,
    build_spartan_checks,
    build_payroll_checks,
    _df_to_records,
)
from logic.bucketing import classify_bucket_type1, classify_bucket_type2

router = APIRouter()


def _safe_records(df: pd.DataFrame) -> list[dict]:
    """Convert DataFrame to JSON-safe records (handle NaN, Inf, Timestamp, numpy types)."""
    import math
    if df is None or df.empty:
        return []
    out = df.copy()
    for col in out.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        out[col] = out[col].dt.strftime("%Y-%m-%d").where(out[col].notna(), None)
    records = out.to_dict(orient="records")

    def _clean(v):
        if v is None:
            return None
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                return None
            return v
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            return None if (np.isnan(v) or np.isinf(v)) else float(v)
        if isinstance(v, np.bool_):
            return bool(v)
        if isinstance(v, float):  # belt-and-suspenders
            return None if math.isnan(v) else v
        return v

    return [{k: _clean(v) for k, v in row.items()} for row in records]


def _people_by_bucket(df: pd.DataFrame, ids: set[str], all_buckets: list[str]) -> dict[str, list[dict]]:
    """Pre-compute people lists for every expanded bucket label."""
    result: dict[str, list[dict]] = {}
    # Standard top-level labels
    labels = ["Grand total", "Delivery", "CXO", "Support Functions"] + all_buckets
    for lab in labels:
        buckets = expand_bucket_selection(lab, all_buckets)
        ppl = people_for_ids_and_buckets(df, ids, buckets)
        if not ppl.empty:
            ppl = ppl.drop(columns=["BUCKET"], errors="ignore")
            result[lab] = _safe_records(ppl)
    return result


def _hier_rows_to_dicts(table: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in table.iterrows():
        d = row.to_dict()
        rowtype = d.pop("_rowtype", "child")
        label = d.pop("Headcount", "")
        rows.append({"label": label, "rowtype": rowtype, "values": d})
    return rows


def _recon_rows_to_dicts(table: pd.DataFrame) -> list[dict]:
    return _safe_records(table.drop(columns=["_rowtype"], errors="ignore"))


@router.post("/process")
async def process_dashboard(
    hrms_files: list[UploadFile] = File(...),
    spartan_file: Optional[UploadFile] = File(None),
    payroll_file: Optional[UploadFile] = File(None),
    payroll_start: Optional[str] = Form(None),
    payroll_end: Optional[str] = Form(None),
):
    warnings: list[dict] = []

    # ── 1. Parse and validate HRMS uploads ────────────────────────────────────
    if len(hrms_files) < 2:
        raise HTTPException(422, "At least 2 HRMS files are required.")

    snapshots_raw: list[dict] = []
    invalid_names: list[str] = []

    for uf in hrms_files:
        parsed = validate_hrms_filename(uf.filename or "")
        if parsed is None:
            invalid_names.append(uf.filename or "")
            continue
        year, month, day = parsed
        file_bytes = await uf.read()
        snapshots_raw.append({
            "filename": uf.filename,
            "file_bytes": file_bytes,
            "year": year,
            "month": month,
            "day": day,
            "month_key": (year, month, day),
            "month_short": format_snapshot_date(year, month, day),
        })

    if invalid_names:
        raise HTTPException(
            422,
            f"Invalid HRMS filename(s): {invalid_names}. "
            "Required format: HRMS_YYYY_MM_DD.xlsx",
        )

    if len(snapshots_raw) < 2:
        raise HTTPException(422, "At least 2 valid HRMS files are required.")

    snapshots_raw.sort(key=lambda x: x["month_key"])
    for i, s in enumerate(snapshots_raw):
        s["snapshot_order"] = i

    # ── 2. Load all snapshots ─────────────────────────────────────────────────
    loaded: list[dict] = []
    for snap in snapshots_raw:
        try:
            df, counts, file_type = load_snapshot(snap["file_bytes"], is_previous=False)
            loaded.append({**snap, "df": df, "counts": counts, "file_type": file_type})
        except Exception as e:
            raise HTTPException(422, f"{snap['filename']}: {e}")

    snapshot_metas = [
        {
            "label": s["month_short"],
            "month_key": list(s["month_key"]),
            "file_name": s["filename"],
        }
        for s in loaded
    ]

    # ── 3. Spartan & Payroll ──────────────────────────────────────────────────
    spartan_df: pd.DataFrame | None = None
    spartan_active_ids: set[str] = set()
    spartan_report: dict | None = None

    if spartan_file is not None:
        sp_bytes = await spartan_file.read()
        try:
            spartan_df, spartan_active_ids, spartan_report = process_spartan_file(sp_bytes)
        except Exception as e:
            raise HTTPException(422, f"Spartan file error: {e}")

    payroll_df: pd.DataFrame | None = None
    payroll_ids: set[str] = set()

    if payroll_file is not None:
        pay_bytes = await payroll_file.read()
        try:
            payroll_df, payroll_ids = process_payroll_file(pay_bytes)
        except Exception as e:
            warnings.append({"file": payroll_file.filename, "message": str(e)})

    pay_start = date.fromisoformat(payroll_start) if payroll_start else date.today().replace(day=1)
    pay_end = date.fromisoformat(payroll_end) if payroll_end else date.today()

    # ── 4. Trend ──────────────────────────────────────────────────────────────
    trend_df = build_metric_trend(loaded)
    trend = {
        "labels": trend_df["Month"].tolist(),
        "total": trend_df["Total headcount"].tolist(),
        "delivery": trend_df["Delivery"].tolist(),
        "support": trend_df["Support Functions"].tolist(),
        "cxo": trend_df["CXO"].tolist(),
    }

    # ── 5. Overview table (consecutive pairs) ─────────────────────────────────
    overview_rows: list[dict] = []
    for i in range(len(loaded) - 1):
        base_s, end_s = loaded[i], loaded[i + 1]
        table = build_hier_table(base_s["counts"], end_s["counts"], base_s["month_short"], end_s["month_short"])

        def v(label: str, col: str):
            rows_match = table.loc[table["Headcount"] == label, col]
            return int(rows_match.iloc[0]) if not rows_match.empty else 0

        base_lbl, end_lbl = base_s["month_short"], end_s["month_short"]
        base_total = v("Grand total", base_lbl)
        end_total = v("Grand total", end_lbl)
        delivery_base = v("Delivery", base_lbl)
        delivery_end = v("Delivery", end_lbl)
        cxo_base = v("CXO", base_lbl)
        cxo_end = v("CXO", end_lbl)
        support_base = v("Support Functions", base_lbl)
        support_end = v("Support Functions", end_lbl)

        def pct(a, b):
            if a == 0 and b == 0:
                return None
            return None if a == 0 else round((b - a) / a * 100, 1)

        overview_rows.append({
            "start_month": base_lbl,
            "end_month": end_lbl,
            "start_hc": base_total,
            "end_hc": end_total,
            "abs_change": end_total - base_total,
            "pct_change": pct(base_total, end_total),
            "pct_change_delivery": pct(delivery_base, delivery_end),
            "pct_change_cxo": pct(cxo_base, cxo_end),
            "pct_change_support": pct(support_base, support_end),
        })

    # ── 6. Pair tables (all combinations) ────────────────────────────────────
    pair_tables: dict[str, dict] = {}
    for i in range(len(loaded)):
        for j in range(i + 1, len(loaded)):
            start_s, end_s = loaded[i], loaded[j]
            key = f"{start_s['month_short']} → {end_s['month_short']}"
            table = build_hier_table(start_s["counts"], end_s["counts"], start_s["month_short"], end_s["month_short"])

            start_ids = set(start_s["df"]["EMPLOYEE ID"].astype(str))
            end_ids = set(end_s["df"]["EMPLOYEE ID"].astype(str))
            all_buckets = sorted(set(start_s["df"]["BUCKET"]).union(set(end_s["df"]["BUCKET"])))

            pair_tables[key] = {
                "start_label": start_s["month_short"],
                "end_label": end_s["month_short"],
                "hier_rows": _hier_rows_to_dicts(table),
                "start_people": _people_by_bucket(start_s["df"], start_ids, all_buckets),
                "end_people": _people_by_bucket(end_s["df"], end_ids, all_buckets),
            }

    # ── 7. Reconciliation tables ──────────────────────────────────────────────
    reconciliation_tables: dict[str, dict] = {}
    for i in range(len(loaded)):
        for j in range(i + 1, len(loaded)):
            base_s, end_s = loaded[i], loaded[j]
            key = f"{base_s['month_short']} → {end_s['month_short']}"

            base_ids = set(base_s["df"]["EMPLOYEE ID"].astype(str))
            end_ids = set(end_s["df"]["EMPLOYEE ID"].astype(str))

            sep_only = base_ids - end_ids
            spartan_exit_ids = sep_only & spartan_active_ids
            bau_attrition_ids = sep_only - spartan_exit_ids
            new_hire_ids = end_ids - base_ids

            base_counts_rec = base_s["df"].groupby("BUCKET")["EMPLOYEE ID"].nunique()
            rec_table = build_reconciliation_table(
                base_counts=base_counts_rec,
                spartan_counts=counts_from_ids(base_s["df"], spartan_exit_ids),
                bau_counts=counts_from_ids(base_s["df"], bau_attrition_ids),
                hire_counts=counts_from_ids(end_s["df"], new_hire_ids),
                end_counts=end_s["df"].groupby("BUCKET")["EMPLOYEE ID"].nunique(),
                base_label=f"{base_s['month_short']} (Baseline)",
                spartan_label=f"-Spartan exits till {end_s['month_short']}",
                bau_label="-BAU attrition",
                hire_label="-New hires",
                end_label=f"{end_s['month_short']} (End-point)",
            )

            all_buckets = sorted(set(base_s["df"]["BUCKET"]).union(set(end_s["df"]["BUCKET"])))

            reconciliation_tables[key] = {
                "base_label": base_s["month_short"],
                "end_label": end_s["month_short"],
                "rows": _recon_rows_to_dicts(rec_table),
                "baseline_people": _people_by_bucket(base_s["df"], base_ids, all_buckets),
                "spartan_exit_people": _people_by_bucket(base_s["df"], spartan_exit_ids, all_buckets),
                "bau_attrition_people": _people_by_bucket(base_s["df"], bau_attrition_ids, all_buckets),
                "new_hire_people": _people_by_bucket(end_s["df"], new_hire_ids, all_buckets),
                "end_people": _people_by_bucket(end_s["df"], end_ids, all_buckets),
            }

    # ── 8. Span data ──────────────────────────────────────────────────────────
    # Collect raw DFs for span (re-read from bytes to avoid post-prepare_hr_snapshot mutation)
    span_snapshots: list[dict] = []
    for snap in loaded:
        try:
            raw_df = read_excel_best_sheet(io.BytesIO(snap["file_bytes"])).dropna(how="all")
        except Exception:
            raw_df = snap["df"]
        span_snapshots.append({
            **snap,
            "raw_df": raw_df,
        })

    # Collect unknown grades union across all snapshots
    all_unknown: set[str] = set()
    for snap in span_snapshots:
        try:
            _, _, _, unk = span_prepare_and_detect_unknown(snap["raw_df"])
            all_unknown |= unk
        except Exception:
            pass

    # Trend by cluster (no unknown grade overrides at this stage — frontend will re-request if needed)
    cluster_mapping = None  # No folder-based mapping when using uploads; could add as optional upload
    trend_long_df = span_trend_ic_tl_by_cluster(span_snapshots, cluster_mapping, {})

    # Service line tables
    try:
        sl_wide = span_service_line_wide_table(span_snapshots)
        sl_span_wide, sl_role_wide = span_service_line_span_and_role_counts(span_snapshots)
    except Exception as e:
        warnings.append({"file": "span", "message": f"Service line computation failed: {e}"})
        sl_wide = sl_span_wide = sl_role_wide = pd.DataFrame()

    # Single snapshot detail (last snapshot)
    last_snap = span_snapshots[-1]
    single_roles: list[dict] = []
    cluster_summary_rows: list[dict] = []
    cluster_status = ""
    try:
        conneqt_df, rc, _, _ = span_prepare_and_detect_unknown(last_snap["raw_df"])
        if not conneqt_df.empty:
            role_s = span_classify_ic_tl_m1(conneqt_df, rc)
            out_df = conneqt_df.copy()
            out_df["IC / TL / M1+"] = role_s.values
            out_clustered, cluster_summary, cluster_status = span_attach_cluster_and_summarize(out_df, cluster_mapping)
            single_roles = _safe_records(out_df)
            if cluster_summary is not None and not cluster_summary.empty:
                cluster_summary_rows = _safe_records(cluster_summary)
    except Exception as e:
        warnings.append({"file": "span_single", "message": str(e)})

    span_data = {
        "unknown_grades": sorted(all_unknown),
        "trend_long": _safe_records(trend_long_df),
        "service_line_counts": _safe_records(sl_wide),
        "service_line_span": _safe_records(sl_span_wide),
        "service_line_roles": _safe_records(sl_role_wide),
        "single_snapshot_label": last_snap["month_short"],
        "single_snapshot_roles": single_roles,
        "cluster_summary": cluster_summary_rows,
        "cluster_status": cluster_status,
    }

    # ── 9. Spartan/HRMS checks ────────────────────────────────────────────────
    spartan_checks: dict[str, dict] = {}
    for i in range(len(loaded)):
        for j in range(i + 1, len(loaded)):
            base_s, end_s = loaded[i], loaded[j]
            key = f"{base_s['month_short']} → {end_s['month_short']}"
            end_date = date(end_s["year"], end_s["month"], end_s["day"])

            spartan_result = build_spartan_checks(
                base_s["df"], end_s["df"],
                spartan_df, spartan_active_ids,
                end_date,
            )

            payroll_result = build_payroll_checks(
                spartan_df, payroll_df, payroll_ids,
                pay_start, pay_end,
            )

            spartan_checks[key] = {
                "spartan_available": spartan_result["spartan_available"],
                "spartan_report": spartan_report,
                "spartan_exit_count": spartan_result["spartan_exit_count"],
                "bau_attrition_count": spartan_result["bau_attrition_count"],
                "new_hire_count": spartan_result["new_hire_count"],
                "offenders_hrms": spartan_result.get("offenders_hrms", []),
                "offenders_hrms_count": spartan_result.get("offenders_hrms_count", 0),
                "overdue_spartan": spartan_result.get("overdue_spartan", []),
                "overdue_spartan_count": spartan_result.get("overdue_spartan_count", 0),
                "payroll": payroll_result,
            }

    # ── 10. Build final response ──────────────────────────────────────────────
    return {
        "snapshots": snapshot_metas,
        "trend": trend,
        "overview_table": overview_rows,
        "pair_tables": pair_tables,
        "reconciliation_tables": reconciliation_tables,
        "span": span_data,
        "spartan_checks": spartan_checks,
        "validation_warnings": warnings,
    }
