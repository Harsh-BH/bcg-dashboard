from datetime import date

import pandas as pd

from logic.utils import to_id_string, clean_text_series, read_spartan_auto, read_payroll_auto
from logic.normalization import normalize_spartan_cols, normalize_payroll_cols


def process_spartan_file(file_bytes: bytes) -> tuple[pd.DataFrame, set[str], dict]:
    """
    Parse and normalize a D2 Spartan upload.
    Returns (spartan_df, active_ids, report_meta).
    active_ids = IDs where D3 == 1 (or all IDs if no D3 column).
    """
    sp_raw, sp_sheet, sp_header = read_spartan_auto(file_bytes)
    spartan_df = normalize_spartan_cols(sp_raw.dropna(how="all"))

    if "EMPLOYEE ID" not in spartan_df.columns:
        raise ValueError(
            f"D2 Spartan missing Employee ID column. "
            f"Found: {list(spartan_df.columns)}. Sheet: {sp_sheet}, header row: {sp_header + 1}"
        )

    spartan_df["EMPLOYEE ID"] = spartan_df["EMPLOYEE ID"].map(to_id_string)
    spartan_df = spartan_df[spartan_df["EMPLOYEE ID"].notna()].copy()

    if "SPARTAN CATEGORY" in spartan_df.columns:
        spartan_df["SPARTAN CATEGORY"] = clean_text_series(spartan_df["SPARTAN CATEGORY"]).fillna("")
    if "LWD" in spartan_df.columns:
        spartan_df["LWD"] = pd.to_datetime(spartan_df["LWD"], errors="coerce")
    else:
        spartan_df["LWD"] = pd.NaT

    if "D3" in spartan_df.columns:
        d3_raw = clean_text_series(spartan_df["D3"]).fillna("").astype(str).str.strip().str.lower()
        d3_num = pd.to_numeric(d3_raw, errors="coerce")
        d3_is_one = (d3_num.eq(1) | d3_raw.eq("1")).fillna(False)
        spartan_df = spartan_df[d3_is_one].copy()

    active_ids = set(spartan_df["EMPLOYEE ID"].astype(str))
    report = {"sheet_used": sp_sheet, "header_row": sp_header + 1}
    return spartan_df, active_ids, report


def process_payroll_file(file_bytes: bytes) -> tuple[pd.DataFrame, set[str]]:
    """
    Parse and normalize a Payroll upload.
    Returns (payroll_df, payroll_ids).
    """
    pay_raw, _, _ = read_payroll_auto(file_bytes)
    payroll_df = normalize_payroll_cols(pay_raw.dropna(how="all"))

    if "EMPLOYEE ID" not in payroll_df.columns:
        raise ValueError(
            f"Payroll file missing Employee ID column. Found: {list(payroll_df.columns)}"
        )

    payroll_df["EMPLOYEE ID"] = payroll_df["EMPLOYEE ID"].map(to_id_string)
    payroll_df = payroll_df[payroll_df["EMPLOYEE ID"].notna()].copy()
    payroll_ids = set(payroll_df["EMPLOYEE ID"].astype(str))
    return payroll_df, payroll_ids


def build_spartan_checks(
    base_df: pd.DataFrame,
    end_df: pd.DataFrame,
    spartan_df: pd.DataFrame | None,
    spartan_active_ids: set[str],
    end_date: date,
) -> dict:
    """
    Run all D2 Spartan cross-check logic for a (base, end) snapshot pair.
    Returns a dict of result DataFrames and metrics.
    """
    base_ids = set(base_df["EMPLOYEE ID"].astype(str))
    end_ids = set(end_df["EMPLOYEE ID"].astype(str))

    sep_only_ids = base_ids - end_ids
    spartan_exit_ids = sep_only_ids & spartan_active_ids
    bau_attrition_ids = sep_only_ids - spartan_exit_ids
    new_hire_ids = end_ids - base_ids

    result: dict = {
        "spartan_exit_count": len(spartan_exit_ids),
        "bau_attrition_count": len(bau_attrition_ids),
        "new_hire_count": len(new_hire_ids),
        "spartan_exit_ids": list(spartan_exit_ids),
        "bau_attrition_ids": list(bau_attrition_ids),
        "new_hire_ids": list(new_hire_ids),
        "sp1": [],
        "offenders_hrms": [],
        "sp2": [],
        "overdue_spartan": [],
        "spartan_available": spartan_df is not None,
    }

    if spartan_df is not None:
        hrms_ids = set(end_df["EMPLOYEE ID"].dropna().astype(str))

        sp1 = spartan_df.copy()
        sp1["Exists in current HRMS?"] = sp1["EMPLOYEE ID"].astype(str).isin(hrms_ids)
        offenders_hrms = sp1[sp1["Exists in current HRMS?"]].copy()

        sp2 = pd.DataFrame()
        overdue_spartan = pd.DataFrame()

        if "SPARTAN CATEGORY" in sp1.columns:
            pending = sp1["SPARTAN CATEGORY"].str.lower().str.strip().eq("closed - lwd yet to be completed")
            sp2 = sp1[pending].copy()
            sp2["LWD before current snapshot?"] = sp2["LWD"].notna() & (sp2["LWD"].dt.date < end_date)
            overdue_spartan = sp2[sp2["LWD before current snapshot?"]].copy()

        result["sp1"] = _df_to_records(sp1)
        result["offenders_hrms"] = _df_to_records(offenders_hrms)
        result["sp2"] = _df_to_records(sp2)
        result["overdue_spartan"] = _df_to_records(overdue_spartan)
        result["offenders_hrms_count"] = len(offenders_hrms)
        result["overdue_spartan_count"] = len(overdue_spartan)

    return result


def build_payroll_checks(
    spartan_df: pd.DataFrame | None,
    payroll_df: pd.DataFrame | None,
    payroll_ids: set[str],
    payroll_cycle_start: date,
    payroll_cycle_end: date,
) -> dict:
    """
    Cross-check Spartan (D3=1) file against Payroll file.
    Flags Spartan employees who are still in payroll AND whose LWD <= payroll cycle end.
    Matches the reference Streamlit app Tab 4 payroll logic exactly.
    """
    if payroll_df is None:
        return {"payroll_available": False}
    if spartan_df is None:
        return {"payroll_available": False, "spartan_required": True}

    tmp = spartan_df.copy()
    tmp["EMPLOYEE ID"] = tmp["EMPLOYEE ID"].astype(str)
    tmp["In payroll?"] = tmp["EMPLOYEE ID"].isin(payroll_ids)

    if "LWD" not in tmp.columns:
        tmp["LWD"] = pd.NaT
    tmp["LWD <= payroll cycle end?"] = tmp["LWD"].notna() & (tmp["LWD"].dt.date <= payroll_cycle_end)

    flagged = tmp[tmp["In payroll?"] & tmp["LWD <= payroll cycle end?"]].copy()

    return {
        "payroll_available": True,
        "payroll_cycle_start": str(payroll_cycle_start),
        "payroll_cycle_end": str(payroll_cycle_end),
        "payroll_count": len(payroll_ids),
        "flagged_count": len(flagged),
        "flagged": _df_to_records(flagged),
    }


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    # Convert Timestamps to ISO strings for JSON serialization
    out = df.copy()
    for col in out.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns:
        out[col] = out[col].dt.strftime("%Y-%m-%d").where(out[col].notna(), None)
    return out.where(pd.notnull(out), None).to_dict(orient="records")
