"""
GET /api/drill  — on-demand people list for a clicked cell.

The /process endpoint stores processed snapshot DataFrames in SESSION_CACHE
keyed by session_id. This endpoint filters and returns the people list for
a specific (snapshot label, bucket/category) combination.
"""
from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

# Shared in-memory cache — populated by /process, consumed here.
# Key: session_id (hash of uploaded file bytes)
# Value: dict[label -> pd.DataFrame]
SESSION_CACHE: dict[str, dict[str, pd.DataFrame]] = {}

router = APIRouter()

CATEGORY_TO_BUCKETS: dict[str, list[str]] = {
    "Grand total":       [],          # empty = all
    "Delivery":          ["Conneqt Business Solution", "Alldigi", "Tech & Digital"],
    "CXO":               ["CXO"],
    "Support Functions": [],          # filled dynamically
}


def _safe_records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    out = df.copy()
    for col in out.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        out[col] = out[col].dt.strftime("%Y-%m-%d").where(out[col].notna(), None)
    records = out.to_dict(orient="records")

    def _clean(v):
        if v is None:
            return None
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            return None if (np.isnan(v) or np.isinf(v)) else float(v)
        if isinstance(v, np.bool_):
            return bool(v)
        return v

    return [{k: _clean(v) for k, v in row.items()} for row in records]


def _filter_people(
    df: pd.DataFrame,
    category: str,
    id_filter: Optional[set[str]] = None,
) -> list[dict]:
    """Return people rows for the given category/bucket label."""
    out = df.copy()

    if id_filter is not None:
        out = out[out["EMPLOYEE ID"].astype(str).isin(id_filter)]

    if category == "Grand total":
        pass  # no bucket filter
    elif category == "Delivery":
        out = out[out["BUCKET"].isin(["Conneqt Business Solution", "Alldigi", "Tech & Digital"])]
    elif category == "CXO":
        out = out[out["BUCKET"] == "CXO"]
    elif category.startswith("Support"):
        out = out[out["BUCKET"].str.startswith("Support", na=False)]
    else:
        # Exact bucket match
        out = out[out["BUCKET"] == category]

    cols = [c for c in out.columns if c not in ("BUCKET",)]
    return _safe_records(out[cols].head(5000))  # cap at 5k rows per request


@router.get("/drill")
def drill(
    session_id: str = Query(...),
    snapshot_label: str = Query(...),
    category: str = Query(...),
    id_set: str = Query("all"),  # "all" | comma-separated employee IDs
):
    """
    Return the people list for a drill-down click.

    session_id      — returned by /process
    snapshot_label  — e.g. "Sep 2025"
    category        — "Grand total" | "Delivery" | "CXO" | "Support Functions"
                      | exact bucket name e.g. "Conneqt Business Solution"
    id_set          — "all" or comma-separated employee IDs
                      (used for reconciliation: exits, new hires, etc.)
    """
    if session_id not in SESSION_CACHE:
        raise HTTPException(404, "Session expired or not found. Re-upload files.")

    snap_map = SESSION_CACHE[session_id]
    if snapshot_label not in snap_map:
        available = list(snap_map.keys())
        raise HTTPException(404, f"Snapshot '{snapshot_label}' not found. Available: {available}")

    df = snap_map[snapshot_label]

    id_filter: Optional[set[str]] = None
    if id_set and id_set != "all":
        id_filter = set(id_set.split(","))

    people = _filter_people(df, category, id_filter)
    return {"people": people, "total": len(people)}
