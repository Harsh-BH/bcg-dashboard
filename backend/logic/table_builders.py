from __future__ import annotations
import numpy as np
import pandas as pd

from logic.constants import (
    BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG, BUCKET_CXO, SUPPORT_PREFIX,
)
from logic.utils import salary_series_from_df, salary_series_from_ids


def build_hier_table(
    prev_counts: pd.Series,
    curr_counts: pd.Series,
    prev_label: str,
    curr_label: str,
) -> pd.DataFrame:
    all_buckets = sorted(set(prev_counts.index).union(set(curr_counts.index)))

    delivery_children = [BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG]
    support_children = [b for b in all_buckets if b not in delivery_children and b != BUCKET_CXO]

    support_sorted = []
    if SUPPORT_PREFIX + "HR" in support_children:
        support_sorted.append(SUPPORT_PREFIX + "HR")
    support_sorted.extend(sorted([b for b in support_children if b != SUPPORT_PREFIX + "HR"]))

    def get_count(series: pd.Series, key: str) -> int:
        return int(series.get(key, 0))

    rows = []
    prev_total = int(prev_counts.sum())
    curr_total = int(curr_counts.sum())
    rows.append(("Grand total", prev_total, curr_total, "grand"))

    prev_delivery = sum(get_count(prev_counts, k) for k in delivery_children)
    curr_delivery = sum(get_count(curr_counts, k) for k in delivery_children)
    rows.append(("Delivery", prev_delivery, curr_delivery, "header"))

    for child in delivery_children:
        rows.append((f"  {child}", get_count(prev_counts, child), get_count(curr_counts, child), "child"))

    rows.append((BUCKET_CXO, get_count(prev_counts, BUCKET_CXO), get_count(curr_counts, BUCKET_CXO), "header"))

    prev_support = prev_total - prev_delivery - get_count(prev_counts, BUCKET_CXO)
    curr_support = curr_total - curr_delivery - get_count(curr_counts, BUCKET_CXO)
    rows.append(("Support Functions", prev_support, curr_support, "header"))

    for child in support_sorted:
        rows.append((f"  {child}", get_count(prev_counts, child), get_count(curr_counts, child), "child"))

    out = pd.DataFrame(rows, columns=["Headcount", prev_label, curr_label, "_rowtype"])
    out["Abs change"] = out[curr_label] - out[prev_label]
    out["% change"] = np.where(
        out[prev_label] == 0,
        np.where(out[curr_label] == 0, 0.0, 1.0),
        out["Abs change"] / out[prev_label],
    )
    return out


def build_reconciliation_table(
    base_counts: pd.Series,
    spartan_counts: pd.Series,
    bau_counts: pd.Series,
    hire_counts: pd.Series,
    end_counts: pd.Series,
    base_label: str,
    spartan_label: str,
    bau_label: str,
    hire_label: str,
    end_label: str,
) -> pd.DataFrame:
    all_buckets = sorted(
        set(base_counts.index)
        .union(set(spartan_counts.index))
        .union(set(bau_counts.index))
        .union(set(hire_counts.index))
        .union(set(end_counts.index))
    )

    delivery_children = [BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG]
    support_children = [b for b in all_buckets if b not in delivery_children and b != BUCKET_CXO]

    support_sorted = []
    if SUPPORT_PREFIX + "HR" in support_children:
        support_sorted.append(SUPPORT_PREFIX + "HR")
    support_sorted.extend(sorted([b for b in support_children if b != SUPPORT_PREFIX + "HR"]))

    def get_count(series: pd.Series, key: str) -> int:
        return int(series.get(key, 0))

    rows = []

    def add_row(label: str, key: str | None, rowtype: str):
        if key is None:
            b = int(base_counts.sum())
            s = int(spartan_counts.sum())
            a = int(bau_counts.sum())
            h = int(hire_counts.sum())
            e = int(end_counts.sum())
        elif key == "DELIVERY_TOTAL":
            b = sum(get_count(base_counts, k) for k in delivery_children)
            s = sum(get_count(spartan_counts, k) for k in delivery_children)
            a = sum(get_count(bau_counts, k) for k in delivery_children)
            h = sum(get_count(hire_counts, k) for k in delivery_children)
            e = sum(get_count(end_counts, k) for k in delivery_children)
        elif key == "SUPPORT_TOTAL":
            b = int(base_counts.sum()) - sum(get_count(base_counts, k) for k in delivery_children) - get_count(base_counts, BUCKET_CXO)
            s = int(spartan_counts.sum()) - sum(get_count(spartan_counts, k) for k in delivery_children) - get_count(spartan_counts, BUCKET_CXO)
            a = int(bau_counts.sum()) - sum(get_count(bau_counts, k) for k in delivery_children) - get_count(bau_counts, BUCKET_CXO)
            h = int(hire_counts.sum()) - sum(get_count(hire_counts, k) for k in delivery_children) - get_count(hire_counts, BUCKET_CXO)
            e = int(end_counts.sum()) - sum(get_count(end_counts, k) for k in delivery_children) - get_count(end_counts, BUCKET_CXO)
        else:
            b = get_count(base_counts, key)
            s = get_count(spartan_counts, key)
            a = get_count(bau_counts, key)
            h = get_count(hire_counts, key)
            e = get_count(end_counts, key)

        abs_change = e - b
        pct_change = 0.0 if b == 0 and e == 0 else (1.0 if b == 0 else abs_change / b)
        rows.append((label, b, s, a, h, e, abs_change, pct_change, rowtype))

    add_row("Grand total", None, "grand")
    add_row("Delivery", "DELIVERY_TOTAL", "header")
    for child in delivery_children:
        add_row(child, child, "child")

    add_row(BUCKET_CXO, BUCKET_CXO, "header")
    add_row("Support Functions", "SUPPORT_TOTAL", "header")
    for child in support_sorted:
        add_row(child, child, "child")

    return pd.DataFrame(
        rows,
        columns=["Headcount", base_label, spartan_label, bau_label, hire_label, end_label, "Abs. change", "% change", "_rowtype"],
    )


def build_metric_trend(snapshots: list[dict]) -> pd.DataFrame:
    """
    snapshots: list of dicts with keys month_short, counts (pd.Series).
    counts must already be computed before calling this.
    """
    rows = []
    for snap in snapshots:
        counts = snap["counts"]
        total = int(counts.sum())
        delivery = int(
            counts.get(BUCKET_CONNEQT, 0)
            + counts.get(BUCKET_ALLDIGI, 0)
            + counts.get(BUCKET_TECHDIG, 0)
        )
        cxo = int(counts.get(BUCKET_CXO, 0))
        support = total - delivery - cxo
        rows.append({
            "Month": snap["month_short"],
            "Total headcount": total,
            "Delivery": delivery,
            "Support Functions": support,
            "CXO": cxo,
        })
    return pd.DataFrame(rows)


def counts_from_ids(df: pd.DataFrame, ids: set[str]) -> pd.Series:
    if not ids:
        return pd.Series(dtype="int64")
    return df[df["EMPLOYEE ID"].astype(str).isin(ids)].groupby("BUCKET")["EMPLOYEE ID"].nunique()


def expand_bucket_selection(label: str, all_buckets: list[str]) -> list[str]:
    delivery_children = [BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG]
    lab = str(label).strip()
    if lab.lower() == "grand total":
        return list(all_buckets)
    if lab.lower() == "delivery":
        return [b for b in delivery_children if b in all_buckets]
    if lab == BUCKET_CXO:
        return [BUCKET_CXO] if BUCKET_CXO in all_buckets else []
    if lab.lower() == "support functions":
        return [b for b in all_buckets if b not in delivery_children and b != BUCKET_CXO]
    if lab in all_buckets:
        return [lab]
    return [lab] if lab else []


def people_for_ids_and_buckets(df: pd.DataFrame, ids: set[str], buckets: list[str]) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if not ids:
        return pd.DataFrame(columns=df.columns)
    out = df[df["EMPLOYEE ID"].astype(str).isin(ids)].copy()
    if "BUCKET" in out.columns and buckets:
        out = out[out["BUCKET"].astype(str).isin(buckets)].copy()
    return out


def _bucket_series_value(series: "pd.Series | None", key: str) -> float:
    if series is None:
        return np.nan
    return float(series.get(key, 0.0))


def _bucket_series_sum(series: "pd.Series | None", keys: list[str]) -> float:
    if series is None:
        return np.nan
    return float(sum(float(series.get(k, 0.0)) for k in keys))


def _build_bucket_order_from_frames(base_df: pd.DataFrame, end_df: pd.DataFrame):
    all_buckets = sorted(set(base_df["BUCKET"]).union(set(end_df["BUCKET"])))
    delivery_children = [BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG]
    support_children = [b for b in all_buckets if b not in delivery_children and b != BUCKET_CXO]
    support_sorted = []
    if SUPPORT_PREFIX + "HR" in support_children:
        support_sorted.append(SUPPORT_PREFIX + "HR")
    support_sorted.extend(sorted([b for b in support_children if b != SUPPORT_PREFIX + "HR"]))
    return all_buckets, delivery_children, support_sorted


def build_reconciliation_salary_table(
    base_df: pd.DataFrame,
    end_df: pd.DataFrame,
    spartan_exit_ids: set[str],
    bau_attrition_ids: set[str],
    new_hire_ids: set[str],
    base_label: str,
    spartan_label: str,
    bau_label: str,
    hire_label: str,
    end_label: str,
) -> pd.DataFrame:
    """
    Salary reconciliation version of HRMS walk.
    - Baseline / Spartan exits / BAU attrition → base month OTC PA
    - New hires / End-point → end month OTC PA
    If a file does not have OTC PA, the affected columns are NA.
    Values are in ₹ Cr. % change is SIGNED.
    """
    all_buckets, delivery_children, support_sorted = _build_bucket_order_from_frames(base_df, end_df)

    base_salary = salary_series_from_df(base_df)
    spartan_salary = salary_series_from_ids(base_df, spartan_exit_ids)
    bau_salary = salary_series_from_ids(base_df, bau_attrition_ids)
    hire_salary = salary_series_from_ids(end_df, new_hire_ids)
    end_salary = salary_series_from_df(end_df)

    rows = []

    def add_row(label: str, key: str | None, rowtype: str):
        if key is None:
            b = _bucket_series_sum(base_salary, all_buckets)
            s = _bucket_series_sum(spartan_salary, all_buckets)
            a = _bucket_series_sum(bau_salary, all_buckets)
            h = _bucket_series_sum(hire_salary, all_buckets)
            e = _bucket_series_sum(end_salary, all_buckets)
        elif key == "DELIVERY_TOTAL":
            b = _bucket_series_sum(base_salary, delivery_children)
            s = _bucket_series_sum(spartan_salary, delivery_children)
            a = _bucket_series_sum(bau_salary, delivery_children)
            h = _bucket_series_sum(hire_salary, delivery_children)
            e = _bucket_series_sum(end_salary, delivery_children)
        elif key == "SUPPORT_TOTAL":
            b = _bucket_series_sum(base_salary, support_sorted)
            s = _bucket_series_sum(spartan_salary, support_sorted)
            a = _bucket_series_sum(bau_salary, support_sorted)
            h = _bucket_series_sum(hire_salary, support_sorted)
            e = _bucket_series_sum(end_salary, support_sorted)
        else:
            b = _bucket_series_value(base_salary, key)
            s = _bucket_series_value(spartan_salary, key)
            a = _bucket_series_value(bau_salary, key)
            h = _bucket_series_value(hire_salary, key)
            e = _bucket_series_value(end_salary, key)

        if pd.isna(b) or pd.isna(e):
            abs_change = np.nan
            pct_change = np.nan
        else:
            abs_change = e - b
            if b == 0 and e == 0:
                pct_change = 0.0
            elif b == 0:
                pct_change = 1.0
            else:
                pct_change = abs_change / b

        rows.append((label, b, s, a, h, e, abs_change, pct_change, rowtype))

    add_row("Grand total", None, "grand")
    add_row("Delivery", "DELIVERY_TOTAL", "header")
    for child in delivery_children:
        add_row(child, child, "child")
    add_row(BUCKET_CXO, BUCKET_CXO, "header")
    add_row("Support Functions", "SUPPORT_TOTAL", "header")
    for child in support_sorted:
        add_row(child, child, "child")

    return pd.DataFrame(
        rows,
        columns=[
            "Annual salary cost (₹ Cr)",
            base_label, spartan_label, bau_label, hire_label, end_label,
            "Abs. change", "% change", "_rowtype",
        ],
    )
