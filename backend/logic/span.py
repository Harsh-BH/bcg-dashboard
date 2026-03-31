import re
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from logic.constants import (
    BUCKET_CONNEQT,
    SPAN_TL_DESIGNATIONS,
    SPAN_SL_CORE_KEYS,
    SPAN_SERVICE_LINE_ROW_SPEC,
    _SPAN_SERVICE_LINE_RULES_VERSION,
    SEPTEMBER_TL_COLLECTIONS_CLM_PHRASES,
    SEPTEMBER_TL_EXTRA_PHRASES_SL_KEYS,
    SEPTEMBER_TL_EXTRA_PHRASES_CLUSTER_NAMES,
    SEPTEMBER_MEU_NON_TL_DESIGNATIONS,
    CLM_VOICE_PROCESS,
    CLM_BACKOFFICE_PROCESS,
    COLLECTIONS_PROCESS,
    JAN_BO_PROCESSES,
    DEC_CLM_BACKOFFICE_TO_BACKOFFICE_CC,
    DEC_CLM_BACKOFFICE_TO_COLLECTIONS_CC,
    DEC_COLLECTIONS_TO_CLM_CC,
    DEC_COLLECTIONS_TO_BACKOFFICE_CC,
    DEC_CLMVOICE_TO_COLLECTIONS_CC,
    DEC_CLM_TO_DS_OTHERS_CC,
    DEC_FORCE_UNCLASSIFIED_CC,
    BLANK_PROCESS_TO_DS_OTHERS_CC,
    BLANK_PROCESS_TO_DS_OTHERS_ACCOUNT,
    FORCE_UNCLASSIFIED_CC,
    FORCE_UNCLASSIFIED_ACCOUNT,
    DIVISION_CLM_WHEN_PROCESS_BLANK,
    COLLECTIONS_DESIG_TOKENS,
    BACKOFFICE_DESIG_TOKENS,
    DS_OTHERS_DESIG_TOKENS,
    CLM_GENERIC_DESIG_TOKENS,
)
from logic.normalization import normalize_hr_cols, normalize_span_hrms_cols
from logic.bucketing import classify_bucket_type1, classify_bucket_type2, _detect_file_type_from_normalized
from logic.utils import span_normalize_hrms_ids, keyify


# ── helpers ──────────────────────────────────────────────────────────────────

def _span_grade_normalized(grade_series: pd.Series) -> pd.Series:
    return grade_series.astype(str).str.strip().str.lower().str.replace(r"\s+", "", regex=True).fillna("")


def _span_choose_grade_series(df: pd.DataFrame) -> pd.Series:
    g = df.get("GRADE", pd.Series([""] * len(df), index=df.index))
    l = df.get("LEVEL", pd.Series([""] * len(df), index=df.index))
    g_nonempty = g.astype(str).str.strip().replace({"nan": ""}).ne("").sum()
    l_nonempty = l.astype(str).str.strip().replace({"nan": ""}).ne("").sum()
    return g if g_nonempty >= l_nonempty else l


def _span_series_process_contains_manpower(proc_series: pd.Series) -> pd.Series:
    s = proc_series.fillna("").astype(str)
    return s.str.contains("manpower", case=False, regex=False, na=False)


def _series_is_zero_or_blank(s: pd.Series) -> pd.Series:
    """True where value is blank, NaN, 0, or 0.0."""
    n = s.isna()
    s_str = s.astype(str).str.strip().str.lower()
    zero_like = s_str.isin({"", "0", "0.0", "nan", "n/a", "na"})
    num_zero = pd.to_numeric(s, errors="coerce") == 0
    return n | zero_like | num_zero.fillna(False)


def _span_non_manpower_mask(df: pd.DataFrame) -> pd.Series:
    """
    True = keep row (not manpower). Exclude if:
    - PROCESS contains 'manpower', OR
    - MANPOWER CHECK == 1, OR
    - MANPOWER == 1 / yes / y / true.
    """
    keep = pd.Series(True, index=df.index)

    if "PROCESS" in df.columns:
        keep &= ~_span_series_process_contains_manpower(df["PROCESS"])

    if "MANPOWER CHECK" in df.columns:
        mc_raw = df["MANPOWER CHECK"]
        mc_num = pd.to_numeric(mc_raw, errors="coerce")
        keep &= ~((mc_num == 1) | (mc_raw.astype(str).str.strip() == "1"))

    if "MANPOWER" in df.columns:
        mp_raw = df["MANPOWER"]
        mp_num = pd.to_numeric(mp_raw, errors="coerce")
        keep &= ~(
            (mp_num == 1)
            | (
                mp_raw.astype(str)
                .str.strip()
                .str.lower()
                .isin(["1", "yes", "y", "true"])
            )
        )

    return keep.fillna(True)


def _span_designation_normalized(des_series: pd.Series) -> pd.Series:
    return des_series.astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True).fillna("")


def _span_mandatory_tl_designation_match(
    des_norm_lower: pd.Series,
    extra_phrases: frozenset[str] | None = None,
) -> pd.Series:
    """Space-insensitive substring match against SPAN_TL_DESIGNATIONS (and optionally extra_phrases)."""
    base = tuple(p.strip().lower() for p in SPAN_TL_DESIGNATIONS if str(p).strip())
    extras = tuple(p.strip().lower() for p in (extra_phrases or set())) if extra_phrases else ()
    phrases = base + extras
    if not phrases:
        return pd.Series(False, index=des_norm_lower.index)
    patterns = [re.sub(r"\s+", "", p) for p in phrases if re.sub(r"\s+", "", p)]
    if not patterns:
        return pd.Series(False, index=des_norm_lower.index)
    des_compact = des_norm_lower.astype(str).str.replace(r"\s+", "", regex=True)
    joint = "|".join(re.escape(px) for px in patterns)
    return des_compact.str.contains(joint, regex=True, na=False)


def _span_grade_is_a2_family(g_norm: str) -> bool:
    if not g_norm or g_norm == "nan":
        return False
    return g_norm == "a2" or g_norm.startswith("a2.")


def _span_grade_is_a1_family(g_norm: str) -> bool:
    if not g_norm or g_norm == "nan":
        return False
    return g_norm.startswith("a1.")


# ── conneqt mask ─────────────────────────────────────────────────────────────

def span_conneqt_row_mask(raw_hr_df: pd.DataFrame) -> pd.Series:
    hr = normalize_hr_cols(raw_hr_df)
    if "BUSINESS UNIT" not in hr.columns or "BUSINESS" not in hr.columns:
        return pd.Series(False, index=raw_hr_df.index)
    ftype = _detect_file_type_from_normalized(hr)
    if ftype == "type1":
        bucket = classify_bucket_type1(hr)
    else:
        bucket = classify_bucket_type2(hr)
    m = bucket.eq(BUCKET_CONNEQT)
    if not m.index.equals(raw_hr_df.index):
        m = m.reindex(raw_hr_df.index, fill_value=False)
    return m.fillna(False)


# ── extract family detection ──────────────────────────────────────────────────

def detect_service_line_extract_family(df: pd.DataFrame) -> str:
    """Detect extract type: sept_style (UPDATED BUSINESS UNIT + EXCLUSION), dec_style (LEGAL EMPLOYER NAME + MANPOWER), raw_hrms."""
    cols = set(df.columns)
    if {"UPDATED BUSINESS UNIT", "EXCLUSION"}.issubset(cols):
        return "sept_style"
    if {"LEGAL EMPLOYER NAME", "MANPOWER"}.issubset(cols):
        return "dec_style"
    return "raw_hrms"


# ── prepare & detect unknown ─────────────────────────────────────────────────

def _detect_unknown_grades(df: pd.DataFrame) -> tuple[set[str], set[str]]:
    if "GRADE" not in df.columns:
        df["GRADE"] = ""
    if "LEVEL" not in df.columns:
        df["LEVEL"] = ""
    grade_src = _span_choose_grade_series(df)
    all_grades_raw = set(grade_src.astype(str).str.strip().replace({"nan": ""}).unique()) - {""}

    def is_unknown(g_raw: str) -> bool:
        if not g_raw or not str(g_raw).strip():
            return False
        gn = str(g_raw).strip().lower().replace(" ", "")
        if gn in {"pt", "at", "naps", "nats", "int", "a-rt", "p-rt", "a3", "a4", "a5", "cx1"}:
            return False
        if re.fullmatch(r"p[1-7]", gn):
            return False
        if re.fullmatch(r"e[1-8]", gn):
            return False
        if gn.startswith("a1."):
            return False
        if gn == "a2" or gn.startswith("a2."):
            return False
        return True

    unknown_grades = {g for g in all_grades_raw if is_unknown(g)}
    return all_grades_raw, unknown_grades


def _build_reportee_counts(df: pd.DataFrame) -> pd.Series:
    span_normalize_hrms_ids(df)
    emp_id = df["EMPLOYEE ID"]
    mgr_id = df["MANAGER1 ECODE"].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    reportee_counts = mgr_id.dropna().value_counts()
    unique_emp_ids = pd.Index(emp_id.unique())
    return reportee_counts.reindex(unique_emp_ids).fillna(0).astype(int)


def span_prepare_and_detect_unknown(
    raw_hr_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, set[str], set[str]]:
    df = normalize_span_hrms_cols(raw_hr_df)
    if "EMPLOYEE ID" not in df.columns:
        raise ValueError("Span HRMS file must have an EMPLOYEE ID column.")
    if "MANAGER1 ECODE" not in df.columns:
        raise ValueError("Span HRMS file must have a MANAGER1 ECODE column.")

    conneqt_mask = span_conneqt_row_mask(raw_hr_df)
    conneqt_df = df.loc[conneqt_mask].copy()

    if not conneqt_df.empty:
        conneqt_df = conneqt_df.loc[_span_non_manpower_mask(conneqt_df)].copy()

    if conneqt_df.empty:
        return conneqt_df, pd.Series(dtype=int), set(), set()

    span_normalize_hrms_ids(conneqt_df)
    reportee_count_series = _build_reportee_counts(conneqt_df)
    all_grades_raw, unknown_grades = _detect_unknown_grades(conneqt_df)
    return conneqt_df, reportee_count_series, all_grades_raw, unknown_grades


def span_prepare_and_detect_unknown_all_business_units(
    raw_hr_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series, set[str], set[str]]:
    df = normalize_span_hrms_cols(raw_hr_df)
    if "EMPLOYEE ID" not in df.columns:
        raise ValueError("Span HRMS file must have an EMPLOYEE ID column.")
    if "MANAGER1 ECODE" not in df.columns:
        raise ValueError("Span HRMS file must have a MANAGER1 ECODE column.")

    span_df = df.copy()
    if not span_df.empty:
        span_df = span_df.loc[_span_non_manpower_mask(span_df)].copy()

    if span_df.empty:
        return span_df, pd.Series(dtype=int), set(), set()

    span_normalize_hrms_ids(span_df)
    reportee_count_series = _build_reportee_counts(span_df)
    all_grades_raw, unknown_grades = _detect_unknown_grades(span_df)
    return span_df, reportee_count_series, all_grades_raw, unknown_grades


# ── rule 1 (structural) ──────────────────────────────────────────────────────

def span_rule1_ic_tl_m1(all_emp_ids: set[str], direct_reports: dict[str, set[str]]) -> dict[str, str]:
    role: dict[str, str] = {}
    ids = set(all_emp_ids)

    def reps(e: str) -> set[str]:
        return direct_reports.get(e, set())

    changed = True
    while changed:
        changed = False
        for e in ids:
            if e in role:
                continue
            rset = reps(e)
            if not rset:
                role[e] = "IC"
                changed = True
                continue
            if not rset.issubset(role.keys()):
                continue
            role[e] = "TL" if all(role[x] == "IC" for x in rset) else "M1+"
            changed = True

    for e in ids:
        if e not in role:
            role[e] = "IC"
    return role


def span_direct_report_sets(conneqt_df: pd.DataFrame) -> dict[str, set[str]]:
    df = conneqt_df.copy()
    span_normalize_hrms_ids(df)
    emp = df["EMPLOYEE ID"]
    mgr = df["MANAGER1 ECODE"].replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    all_ids = pd.Index(emp.unique())
    edges = pd.DataFrame({"mgr": mgr, "rep": emp})
    edges = edges[edges["mgr"].notna()].copy()
    edges["mgr"] = edges["mgr"].astype(str).str.strip()
    edges = edges[edges["mgr"].isin(set(all_ids))].copy()
    return edges.groupby("mgr")["rep"].agg(lambda s: set(s.astype(str))).to_dict()


# ── classify IC / TL / M1+ ───────────────────────────────────────────────────

def span_classify_ic_tl_m1(
    conneqt_df: pd.DataFrame,
    reportee_count_series=None,
    unknown_grade_to_rule: dict | None = None,
    extra_tl_designation_phrases: frozenset[str] | None = None,
    extra_tl_employee_ids: frozenset[str] | None = None,
    extra_tl_meu_exclusion_phrases: frozenset[str] | None = None,
    extra_tl_meu_employee_ids: frozenset[str] | None = None,
) -> pd.Series:
    _ = reportee_count_series
    df = conneqt_df.copy()
    if "MANAGER1 ECODE" not in df.columns:
        df["MANAGER1 ECODE"] = ""
    span_normalize_hrms_ids(df)
    for col in ("GRADE", "LEVEL", "DESIGNATION"):
        if col not in df.columns:
            df[col] = ""

    grade_src = _span_choose_grade_series(df)
    grades_norm_row = _span_grade_normalized(grade_src)
    grades_raw_row = grade_src.astype(str).fillna("").str.strip()
    des_norm_row = _span_designation_normalized(df["DESIGNATION"])

    unknown_grade_to_rule = unknown_grade_to_rule or {}

    emp_tbl = pd.DataFrame({
        "EMPLOYEE ID": df["EMPLOYEE ID"],
        "_grade_norm": grades_norm_row,
        "_grade_raw": grades_raw_row,
        "_des_norm": des_norm_row,
    })
    emp_tbl["_grade_norm"] = emp_tbl["_grade_norm"].replace({"": pd.NA, "nan": pd.NA})
    emp_tbl["_grade_raw"] = emp_tbl["_grade_raw"].replace({"": pd.NA, "nan": pd.NA})
    emp_tbl["_des_norm"] = emp_tbl["_des_norm"].replace({"": pd.NA, "nan": pd.NA})
    emp_one = (
        emp_tbl.groupby("EMPLOYEE ID", as_index=False)
        .agg({"_grade_norm": "first", "_grade_raw": "first", "_des_norm": "first"})
        .fillna("")
    )

    edges = pd.DataFrame({
        "rep": df["EMPLOYEE ID"],
        "mgr": df["MANAGER1 ECODE"].astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA}),
    })
    edges = edges[edges["mgr"].notna()].copy()
    edges["mgr"] = edges["mgr"].astype(str).str.strip()
    ids_set = set(emp_one["EMPLOYEE ID"].astype(str))
    edges = edges[edges["mgr"].isin(ids_set)].copy()

    n_rep = edges.groupby("mgr")["rep"].nunique()
    eids = emp_one["EMPLOYEE ID"].astype(str)
    emp_one["n_rep"] = eids.map(n_rep).fillna(0).astype(int)

    ugr = unknown_grade_to_rule
    m_raw = emp_one["_grade_raw"].map(ugr)
    m_norm = emp_one["_grade_norm"].map(ugr)
    valid = {"IC", "TL", "M1+"}
    emp_one["forced_role"] = ""
    ok_raw = m_raw.isin(list(valid))
    emp_one.loc[ok_raw, "forced_role"] = m_raw[ok_raw].astype(str)
    ok_norm = ~ok_raw & m_norm.isin(list(valid))
    emp_one.loc[ok_norm, "forced_role"] = m_norm[ok_norm].astype(str)

    g = emp_one["_grade_norm"].astype(str)
    des_l = emp_one["_des_norm"].astype(str).str.lower()
    is_a1_or_a2 = g.str.startswith("a1.") | (g == "a2") | g.str.startswith("a2.")

    # Base TL designation match
    has_tl_desig = _span_mandatory_tl_designation_match(des_l, extra_phrases=None)

    # September extra TL phrases scoped to specific employees
    if extra_tl_designation_phrases:
        extra_match = _span_mandatory_tl_designation_match(des_l, extra_phrases=extra_tl_designation_phrases)
        if extra_tl_employee_ids:
            in_scope = emp_one["EMPLOYEE ID"].astype(str).isin(extra_tl_employee_ids)
            tl_from_extra = in_scope & extra_match
            if extra_tl_meu_exclusion_phrases and extra_tl_meu_employee_ids:
                in_meu = emp_one["EMPLOYEE ID"].astype(str).isin(extra_tl_meu_employee_ids)
                meu_excluded = _span_mandatory_tl_designation_match(des_l, extra_phrases=extra_tl_meu_exclusion_phrases)
                tl_from_extra = tl_from_extra & ~(in_meu & meu_excluded)
            has_tl_desig = has_tl_desig | tl_from_extra
        else:
            has_tl_desig = has_tl_desig | extra_match

    emp_one["mandatory_tl_a1a2"] = is_a1_or_a2 & has_tl_desig

    is_ic_grade = is_a1_or_a2 | g.isin(["pt", "at", "naps", "nats", "int", "a-rt", "p-rt"])
    emp_one["is_ic"] = (emp_one["forced_role"] == "IC") & (emp_one["n_rep"] == 0)
    emp_one.loc[emp_one["forced_role"] == "", "is_ic"] = (
        (emp_one["n_rep"] == 0) & is_ic_grade & ~emp_one["mandatory_tl_a1a2"]
    )

    ic_set = set(emp_one.loc[emp_one["is_ic"], "EMPLOYEE ID"].astype(str))
    edges["rep_is_ic"] = edges["rep"].astype(str).isin(ic_set)
    all_rep_ic = edges.groupby("mgr")["rep_is_ic"].all()
    cond_tl1 = eids.map(all_rep_ic).fillna(False).astype(bool) & (emp_one["n_rep"] >= 1)

    is_a3_or_a4 = emp_one["_grade_norm"].isin(["a3", "a4"])
    cond_tl2 = is_a3_or_a4 & (emp_one["n_rep"] == 0) & ~emp_one["forced_role"].isin(["M1+", "TL"])

    emp_one["is_tl"] = emp_one["forced_role"] == "TL"
    emp_one.loc[emp_one["forced_role"] == "", "is_tl"] = cond_tl1 | cond_tl2

    mand = emp_one["mandatory_tl_a1a2"].to_numpy()
    fr = emp_one["forced_role"].to_numpy()
    icv = emp_one["is_ic"].to_numpy()
    tlv = emp_one["is_tl"].to_numpy()
    n = len(emp_one)
    out_emp = np.full(n, "M1+", dtype=object)
    out_emp[mand] = "TL"
    forced_ok = np.isin(fr, ["IC", "TL", "M1+"]) & ~mand
    out_emp[forced_ok] = fr[forced_ok]
    rest = ~mand & ~forced_ok
    out_emp[rest & icv] = "IC"
    rest2 = rest & ~icv
    out_emp[rest2 & tlv] = "TL"
    emp_one["final_role"] = out_emp

    role_ser = pd.Series(out_emp, index=eids.values)
    out = df["EMPLOYEE ID"].astype(str).map(role_ser).fillna("M1+")
    return pd.Series(out.values, index=conneqt_df.index)


def span_classify_ic_tl_m1_full_graph(
    target_df: pd.DataFrame,
    graph_df: pd.DataFrame,
    unknown_grade_to_rule: dict | None = None,
) -> pd.Series:
    """
    Classify IC / TL / M1+ using the FULL active non-manpower HRMS graph for accurate reportee counts,
    then map the result back to the target_df population.

    IC:   0 direct reportees AND grade in A1.x / A2.x / PT / AT / NAPS / NATS / INT / A-RT / P-RT
    TL:   A1.x/A2.x + TL-like designation
          OR ≥1 direct report and all direct reports are IC
          OR A3/A4 with 0 direct reportees
    M1+:  A5 / E1-E8 / P1-P7 / CX* / CXO  OR  ≥1 report with any TL/M1+ report  OR  default
    """
    if target_df is None or target_df.empty:
        return pd.Series(dtype=object)

    tdf = target_df.copy()
    gdf = graph_df.copy()

    for frame in (tdf, gdf):
        if "MANAGER1 ECODE" not in frame.columns:
            frame["MANAGER1 ECODE"] = ""
        if "GRADE" not in frame.columns:
            frame["GRADE"] = ""
        if "LEVEL" not in frame.columns:
            frame["LEVEL"] = ""
        if "DESIGNATION" not in frame.columns:
            frame["DESIGNATION"] = ""
        span_normalize_hrms_ids(frame)

    unknown_grade_to_rule = unknown_grade_to_rule or {}

    grade_src_all = _span_choose_grade_series(gdf)
    grades_norm_all = _span_grade_normalized(grade_src_all)
    grades_raw_all = grade_src_all.astype(str).fillna("").str.strip()
    des_norm_all = _span_designation_normalized(gdf["DESIGNATION"])

    emp_tbl = pd.DataFrame(
        {
            "EMPLOYEE ID": gdf["EMPLOYEE ID"].astype(str),
            "_grade_norm": grades_norm_all,
            "_grade_raw": grades_raw_all,
            "_des_norm": des_norm_all,
        }
    )
    emp_tbl["_grade_norm"] = emp_tbl["_grade_norm"].replace({"": pd.NA, "nan": pd.NA})
    emp_tbl["_grade_raw"] = emp_tbl["_grade_raw"].replace({"": pd.NA, "nan": pd.NA})
    emp_tbl["_des_norm"] = emp_tbl["_des_norm"].replace({"": pd.NA, "nan": pd.NA})

    emp_one = (
        emp_tbl.groupby("EMPLOYEE ID", as_index=False)
        .agg({"_grade_norm": "first", "_grade_raw": "first", "_des_norm": "first"})
        .fillna("")
    )

    all_ids = set(emp_one["EMPLOYEE ID"].astype(str))

    edges = pd.DataFrame(
        {
            "rep": gdf["EMPLOYEE ID"].astype(str),
            "mgr": gdf["MANAGER1 ECODE"].astype(str).str.strip().replace(
                {"": pd.NA, "nan": pd.NA, "None": pd.NA}
            ),
        }
    )
    edges = edges[edges["mgr"].notna()].copy()
    edges["mgr"] = edges["mgr"].astype(str).str.strip()
    edges = edges[edges["mgr"].isin(all_ids)].copy()

    n_rep = edges.groupby("mgr")["rep"].nunique()
    eids = emp_one["EMPLOYEE ID"].astype(str)
    emp_one["n_rep"] = eids.map(n_rep).fillna(0).astype(int)

    m_raw = emp_one["_grade_raw"].map(unknown_grade_to_rule)
    m_norm = emp_one["_grade_norm"].map(unknown_grade_to_rule)
    valid = {"IC", "TL", "M1+"}
    emp_one["forced_role"] = ""
    ok_raw = m_raw.isin(list(valid))
    emp_one.loc[ok_raw, "forced_role"] = m_raw[ok_raw].astype(str)
    ok_norm = ~ok_raw & m_norm.isin(list(valid))
    emp_one.loc[ok_norm, "forced_role"] = m_norm[ok_norm].astype(str)

    g = emp_one["_grade_norm"].astype(str).str.strip().str.lower()
    des_l = emp_one["_des_norm"].astype(str).str.lower()

    is_a1_or_a2 = g.str.startswith("a1.") | g.eq("a2") | g.str.startswith("a2.")
    is_a3_or_a4 = g.isin(["a3", "a4"])
    high_m1 = g.str.fullmatch(r"a5|e[1-8]|p[1-7]|cx\d+|cxo", na=False)

    has_tl_desig = _span_mandatory_tl_designation_match(des_l)
    mandatory_tl = is_a1_or_a2 & has_tl_desig

    is_ic_grade = is_a1_or_a2 | g.isin(["pt", "at", "naps", "nats", "int", "a-rt", "p-rt"])

    emp_one["is_ic"] = False
    emp_one.loc[emp_one["forced_role"] == "IC", "is_ic"] = emp_one["n_rep"].eq(0)
    emp_one.loc[emp_one["forced_role"] == "", "is_ic"] = (
        emp_one["n_rep"].eq(0) & is_ic_grade & ~mandatory_tl & ~high_m1
    )

    ic_set = set(emp_one.loc[emp_one["is_ic"], "EMPLOYEE ID"].astype(str))

    edges["rep_is_ic"] = edges["rep"].astype(str).isin(ic_set)
    all_rep_ic = edges.groupby("mgr")["rep_is_ic"].all()

    cond_tl_reports = eids.map(all_rep_ic).fillna(False).astype(bool) & emp_one["n_rep"].ge(1) & ~high_m1
    cond_tl_a3a4_leaf = is_a3_or_a4 & emp_one["n_rep"].eq(0) & ~high_m1

    emp_one["is_tl"] = False
    emp_one.loc[emp_one["forced_role"] == "TL", "is_tl"] = True
    emp_one.loc[emp_one["forced_role"] == "", "is_tl"] = mandatory_tl | cond_tl_reports | cond_tl_a3a4_leaf

    out_emp = np.full(len(emp_one), "M1+", dtype=object)

    fm1 = high_m1.to_numpy()
    mand = mandatory_tl.to_numpy()
    fr = emp_one["forced_role"].to_numpy()
    icv = emp_one["is_ic"].to_numpy()
    tlv = emp_one["is_tl"].to_numpy()

    out_emp[fm1] = "M1+"

    remaining = ~fm1
    out_emp[remaining & mand] = "TL"

    forced_ok = remaining & ~mand & np.isin(fr, ["IC", "TL", "M1+"])
    out_emp[forced_ok] = fr[forced_ok]

    rest = remaining & ~mand & ~forced_ok
    out_emp[rest & icv] = "IC"
    rest2 = rest & ~icv
    out_emp[rest2 & tlv] = "TL"

    role_map = pd.Series(out_emp, index=emp_one["EMPLOYEE ID"].astype(str))
    out = tdf["EMPLOYEE ID"].astype(str).map(role_map).fillna("M1+")
    return pd.Series(out.values, index=target_df.index)


# ── cluster mapping ───────────────────────────────────────────────────────────

def find_conneqt_cost_mapping_path(folder_path: str):
    p = Path(folder_path)
    if not p.is_dir():
        return None
    for name in (
        "Conneqt_CostCode_Mapping.xlsx",
        "Conneqt_CostCode_Mapping.xlsm",
        "Conneqt CostCode Mapping.xlsx",
        "Conneqt_Cost_Code_Mapping.xlsx",
    ):
        f = p / name
        if f.is_file():
            return f
    for f in sorted(p.glob("*.xlsx"), key=lambda x: x.name.lower()):
        low = f.name.lower()
        if "conneqt" in low and "cost" in low and "mapp" in low:
            return f
    return None


def _conneqt_mapping_code_cluster_cols(df: pd.DataFrame):
    def ck(c):
        return keyify(str(c)).strip()

    code_col = None
    cluster_col = None
    for c in df.columns:
        if str(c).lower().startswith("unnamed"):
            continue
        k = ck(c)
        if k in ("cost code", "costcode") or ("cost" in k and "code" in k and "cluster" not in k):
            if code_col is None or k in ("cost code", "costcode"):
                code_col = c
        if k == "cluster" and "head" not in k:
            cluster_col = c
    if cluster_col is None:
        for c in df.columns:
            if str(c).lower().startswith("unnamed"):
                continue
            if keyify(str(c)) == "cluster":
                cluster_col = c
                break
    if cluster_col is None:
        col_map = {keyify(c): c for c in df.columns if not str(c).lower().startswith("unnamed")}
        for alias in ("vertical", "cluster name", "business cluster"):
            if alias in col_map:
                cluster_col = col_map[alias]
                break
    return code_col, cluster_col


def _conneqt_mapping_account_col(df: pd.DataFrame) -> str | None:
    col_map = {keyify(str(c)).strip(): c for c in df.columns if not str(c).lower().startswith("unnamed")}
    for alias in ("customer name", "customername", "customer", "account name", "accountname", "account", "client name"):
        if alias in col_map:
            return col_map[alias]
    return None


def _build_cluster_mapping_table(df: pd.DataFrame):
    code_col, cluster_col = _conneqt_mapping_code_cluster_cols(df)
    if code_col is None or cluster_col is None:
        return None
    m = df[[code_col, cluster_col]].dropna(how="all").copy()
    m.columns = ["_code", "_cluster"]
    m["_cc_key"] = m["_code"].astype(str).str.strip().str.upper()
    m["_cluster"] = m["_cluster"].fillna("").astype(str).str.strip()
    m = m[m["_cc_key"].ne("") & m["_cc_key"].ne("NAN")]
    if m.empty:
        return None
    m = m.drop_duplicates(subset=["_cc_key"], keep="first")
    return m.rename(columns={"_cc_key": "cc_key", "_cluster": "Cluster"})[["cc_key", "Cluster"]]


def load_conneqt_cluster_mapping(path_str: str) -> pd.DataFrame:
    xls = pd.ExcelFile(path_str)
    last_cols: list = []
    for sheet in xls.sheet_names:
        for header_row in range(30):
            try:
                d = pd.read_excel(path_str, sheet_name=sheet, header=header_row)
            except Exception:
                continue
            d = d.dropna(how="all")
            if d.empty or len(d.columns) < 2:
                continue
            d.columns = [str(c).strip() for c in d.columns]
            last_cols = list(d.columns)
            if all(str(c).lower().startswith("unnamed") for c in d.columns):
                continue
            out = _build_cluster_mapping_table(d)
            if out is not None and len(out) >= 1:
                return out
    raise ValueError(
        "Conneqt cost mapping file must have Cost code and Cluster columns. "
        f"Last columns seen: {last_cols[:12]}{'…' if len(last_cols) > 12 else ''}"
    )


def load_conneqt_cost_code_account_mapping(path_str: str) -> pd.DataFrame:
    """Read Conneqt_CostCode_Mapping: Cost code → Cluster + Account (Customer Name)."""
    xls = pd.ExcelFile(path_str)
    last_cols: list = []
    for sheet in xls.sheet_names:
        for header_row in range(30):
            try:
                d = pd.read_excel(path_str, sheet_name=sheet, header=header_row)
            except Exception:
                continue
            d = d.dropna(how="all")
            if d.empty or len(d.columns) < 2:
                continue
            d.columns = [str(c).strip() for c in d.columns]
            last_cols = list(d.columns)
            if all(str(c).lower().startswith("unnamed") for c in d.columns):
                continue
            code_col, cluster_col = _conneqt_mapping_code_cluster_cols(d)
            if code_col is None or cluster_col is None:
                continue
            cols_to_use = [code_col, cluster_col]
            account_col = _conneqt_mapping_account_col(d)
            if account_col is not None:
                cols_to_use.append(account_col)
            m = d[cols_to_use].dropna(how="all").copy()
            m.columns = ["_code", "_cluster"] + (["_account"] if account_col else [])
            m["cc_key"] = m["_code"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""})
            m["Cluster"] = m["_cluster"].fillna("").astype(str).str.strip()
            m = m[m["cc_key"].ne("") & m["cc_key"].ne("NAN")]
            if m.empty:
                continue
            if "_account" in m.columns:
                m["Account"] = m["_account"].fillna("").astype(str).str.strip()
            else:
                m["Account"] = ""
            m = m.drop_duplicates(subset=["cc_key"], keep="first")
            return m[["cc_key", "Cluster", "Account"]]
    raise ValueError(
        "Conneqt cost mapping file must have Cost code and Cluster columns. "
        f"Last columns seen: {last_cols[:12]}{'…' if len(last_cols) > 12 else ''}"
    )


def span_attach_cluster_and_summarize(
    out_df: pd.DataFrame,
    cluster_mapping: pd.DataFrame | None,
) -> tuple[pd.DataFrame, pd.DataFrame | None, str]:
    msg_parts = []
    if cluster_mapping is None:
        out = out_df.copy()
        out["Cluster"] = "Unmapped (no mapping file)"
        return out, None, "Cost mapping file not found."

    if "COST CENTER" not in out_df.columns:
        out = out_df.copy()
        out["Cluster"] = "Unmapped (no cost center)"
        return out, None, "HRMS extract has no COST CENTER column after normalization."

    out = out_df.copy()
    out["_cc_key"] = out["COST CENTER"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""})

    # Use only cc_key + Cluster columns for merge (ignore Account if present)
    merge_cols = ["cc_key", "Cluster"] if "Cluster" in cluster_mapping.columns else list(cluster_mapping.columns)
    out = out.merge(cluster_mapping[merge_cols], left_on="_cc_key", right_on="cc_key", how="left", suffixes=("", "_map"))
    out.drop(columns=["cc_key"], errors="ignore", inplace=True)
    n_miss = int(out["Cluster"].isna().sum())
    out["Cluster"] = out["Cluster"].fillna("Unmapped")
    _cl = out["Cluster"].astype(str).str.strip()
    _bad = _cl.str.lower().isin(["", "nan", "none", "nat", "<na>", "#n/a"])
    out.loc[_bad, "Cluster"] = "Unmapped"
    out.drop(columns=["_cc_key"], errors="ignore", inplace=True)
    n_blank = int(_bad.sum())
    if n_miss:
        msg_parts.append(f"{n_miss} row(s) with no matching Cost Code → Unmapped.")
    if n_blank:
        msg_parts.append(f"{n_blank} row(s) matched but Cluster blank → Unmapped.")

    role_col = "IC / TL / M1+"
    if role_col not in out.columns:
        return out, None, " ".join(msg_parts)

    emp_col = "EMPLOYEE ID" if "EMPLOYEE ID" in out.columns else None
    agg_df = out.drop_duplicates(subset=[emp_col], keep="first") if emp_col else out
    pv = (
        agg_df.groupby(["Cluster", role_col], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["IC", "TL", "M1+"], fill_value=0)
    )
    pv["Total rows"] = pv.sum(axis=1)
    pv = pv.reset_index()
    pv["_u"] = pv["Cluster"].eq("Unmapped")
    pv = pv.sort_values(["_u", "Cluster"]).drop(columns=["_u"])
    if "Span (IC÷TL)" not in pv.columns:
        pv["Span (IC÷TL)"] = np.where(pv["TL"] > 0, pv["IC"].astype(float) / pv["TL"].astype(float), np.nan)
    return out, pv, " ".join(msg_parts)


# ── account cluster helpers ──────────────────────────────────────────────────

def _span_hrms_cluster_column_name(columns) -> str | None:
    """Return the name of a column literally named 'Cluster' (case-insensitive) if present."""
    for c in columns:
        if str(c).strip().lower() == "cluster":
            return str(c)
    return None


def _span_account_wise_rename_for_acc_map_merge(
    span_df: pd.DataFrame,
) -> tuple[pd.DataFrame, str | None, str | None]:
    """
    Rename HRMS columns that overlap acc_map (Cluster, Account) before merging so we don't
    get Cluster_x / Cluster_y suffixes.  Returns (frame_for_merge, hrms_cluster_tmp_col, hrms_account_tmp_col).
    """
    s = span_df.copy()
    hrms_cl_tmp: str | None = None
    cl = _span_hrms_cluster_column_name(s.columns)
    if cl is not None:
        hrms_cl_tmp = "__span_hrms_cluster__"
        s = s.rename(columns={cl: hrms_cl_tmp})
    hrms_ac_tmp: str | None = None
    if "Account" in s.columns:
        hrms_ac_tmp = "__span_hrms_account__"
        s = s.rename(columns={"Account": hrms_ac_tmp})
    return s, hrms_cl_tmp, hrms_ac_tmp


def _span_account_cluster_after_costcode_merge(
    span_df: pd.DataFrame,
    merged: pd.DataFrame,
    mo: int,
    *,
    hrms_cluster_tmp_col: str | None = None,
    hrms_account_tmp_col: str | None = None,
) -> pd.DataFrame:
    """
    Set Account and Cluster columns after a left-merge on _cc_key.
    For September (month==9): use ACCOUNT NAME directly from HRMS (not the mapping).
    For all other months: use the merged Account/Cluster from the cost-code mapping.
    """
    out = merged
    if int(mo) == 9:
        if "ACCOUNT NAME" in span_df.columns:
            out["Account"] = span_df["ACCOUNT NAME"].fillna("").astype(str).str.strip().values
            out.loc[out["Account"].eq(""), "Account"] = "— (no account name in file)"
        elif "Account" in out.columns:
            out["Account"] = out["Account"].fillna("").astype(str).str.strip()
            out.loc[out["Account"].eq(""), "Account"] = "— (no account name in mapping)"
        elif hrms_account_tmp_col and hrms_account_tmp_col in out.columns:
            out["Account"] = out[hrms_account_tmp_col].fillna("").astype(str).str.strip().values
            out.loc[out["Account"].eq(""), "Account"] = "— (no account name in mapping)"
        else:
            out["Account"] = "— (no account name in mapping)"

        if hrms_cluster_tmp_col and hrms_cluster_tmp_col in out.columns:
            out["Cluster"] = out[hrms_cluster_tmp_col].fillna("").astype(str).str.strip().values
        elif "Cluster" in out.columns:
            out["Cluster"] = out["Cluster"].fillna("Unmapped").astype(str).str.strip()
        else:
            out["Cluster"] = "Unmapped"
        _cl = out["Cluster"].astype(str).str.strip()
        _bad = _cl.str.lower().isin(["", "nan", "none", "nat", "<na>", "#n/a"])
        out.loc[_bad, "Cluster"] = "Unmapped"
        _drop = [c for c in [hrms_cluster_tmp_col, hrms_account_tmp_col] if c and c in out.columns]
        if _drop:
            out.drop(columns=_drop, errors="ignore", inplace=True)
        return out

    # Non-September: use mapping-derived Account/Cluster
    if "Account" in out.columns:
        out["Account"] = out["Account"].fillna("").astype(str).str.strip()
    elif hrms_account_tmp_col and hrms_account_tmp_col in out.columns:
        out["Account"] = out[hrms_account_tmp_col].fillna("").astype(str).str.strip()
    else:
        out["Account"] = ""
    out.loc[out["Account"].eq(""), "Account"] = "— (no account name in mapping)"

    if "Cluster" in out.columns:
        out["Cluster"] = out["Cluster"].fillna("Unmapped").astype(str).str.strip()
    elif hrms_cluster_tmp_col and hrms_cluster_tmp_col in out.columns:
        out["Cluster"] = out[hrms_cluster_tmp_col].fillna("Unmapped").astype(str).str.strip()
    else:
        out["Cluster"] = "Unmapped"
    _cl = out["Cluster"].astype(str).str.strip()
    _bad = _cl.str.lower().isin(["", "nan", "none", "nat", "<na>", "#n/a"])
    out.loc[_bad, "Cluster"] = "Unmapped"
    _drop = [c for c in [hrms_cluster_tmp_col, hrms_account_tmp_col] if c and c in out.columns]
    if _drop:
        out.drop(columns=_drop, errors="ignore", inplace=True)
    return out


# ── trend by cluster ──────────────────────────────────────────────────────────

def _span_process_series(df: pd.DataFrame) -> pd.Series:
    """PROCESS series; falls back to AGG SERVICE LINE when PROCESS missing."""
    n = len(df)
    idx = df.index
    if "PROCESS" in df.columns:
        proc = df["PROCESS"].fillna("").astype(str)
        if "AGG SERVICE LINE" in df.columns:
            agg = df["AGG SERVICE LINE"].fillna("").astype(str)
            proc = proc.where(proc.str.strip().ne(""), agg)
        return proc
    if "AGG SERVICE LINE" in df.columns:
        return df["AGG SERVICE LINE"].fillna("").astype(str)
    return pd.Series([""] * n, index=idx)


def _span_emp_ids_for_clusters(
    df: pd.DataFrame,
    cluster_mapping: pd.DataFrame | None,
    cluster_names: frozenset[str],
) -> frozenset[str]:
    """Return employee IDs whose COST CENTER maps to one of the given cluster names."""
    if cluster_mapping is None or "COST CENTER" not in df.columns or "EMPLOYEE ID" not in df.columns:
        return frozenset()
    cluster_upper = {c.strip().upper() for c in cluster_names if c}
    mee = cluster_mapping["Cluster"].fillna("").astype(str).str.strip().str.upper()
    cc_keys = set(cluster_mapping.loc[mee.isin(cluster_upper), "cc_key"].dropna().astype(str).str.strip().unique()) - {"", "NAN"}
    if not cc_keys:
        return frozenset()
    cc_col = df["COST CENTER"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""})
    mask = cc_col.isin(cc_keys)
    if not mask.any():
        return frozenset()
    return frozenset(df.loc[mask, "EMPLOYEE ID"].astype(str).unique())


def span_trend_ic_tl_by_cluster(
    snapshots: list[dict],
    cluster_mapping: pd.DataFrame | None,
    unknown_grade_choices: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Returns long-format DataFrame (one row per snapshot × Cluster).
    Filters to Core Delivery only (SPAN_SL_CORE_KEYS) before cluster aggregation.
    September snapshots (month==9) get extra TL designation phrases.
    """
    unknown_grade_choices = unknown_grade_choices or {}
    pieces: list[pd.DataFrame] = []

    for i, snap in enumerate(snapshots):
        raw_df = snap["raw_df"]
        mo = int(snap.get("month", 0))
        conneqt_df, rc, _, _ = span_prepare_and_detect_unknown(raw_df)
        if conneqt_df.empty:
            continue

        # September: extra TL phrases for Collections/CLM/WFM/Quality/Training + MEU cluster
        extra_sept: frozenset[str] | None = SEPTEMBER_TL_COLLECTIONS_CLM_PHRASES if mo == 9 else None
        extra_emp_ids: frozenset[str] | None = None
        meu_ids: frozenset[str] | None = None
        if extra_sept:
            proc = _span_process_series(conneqt_df)
            div = conneqt_df.get("DIVISION")
            jf = conneqt_df.get("JOB_FUNCTION")
            des = conneqt_df.get("DESIGNATION")
            acc = conneqt_df.get("ACCOUNT NAME")
            cc = conneqt_df.get("COST CENTER")
            extract_family = detect_service_line_extract_family(conneqt_df)
            keys = span_service_line_keys_series(proc, div, jf, des, acc, cc, extract_family)
            sl_mask = keys.astype(str).isin(SEPTEMBER_TL_EXTRA_PHRASES_SL_KEYS)
            if sl_mask.any() and "EMPLOYEE ID" in conneqt_df.columns:
                extra_emp_ids = frozenset(conneqt_df.loc[sl_mask, "EMPLOYEE ID"].astype(str).unique())
            meu_ids = _span_emp_ids_for_clusters(conneqt_df, cluster_mapping, SEPTEMBER_TL_EXTRA_PHRASES_CLUSTER_NAMES)
            extra_emp_ids = (extra_emp_ids or frozenset()) | meu_ids

        role_s = span_classify_ic_tl_m1(
            conneqt_df,
            rc,
            unknown_grade_to_rule=unknown_grade_choices,
            extra_tl_designation_phrases=extra_sept,
            extra_tl_employee_ids=extra_emp_ids,
            extra_tl_meu_exclusion_phrases=SEPTEMBER_MEU_NON_TL_DESIGNATIONS if (extra_sept and meu_ids) else None,
            extra_tl_meu_employee_ids=meu_ids if extra_sept else None,
        )
        if role_s.empty or len(role_s) != len(conneqt_df):
            continue

        out_df = conneqt_df.copy()
        out_df["IC / TL / M1+"] = role_s.values

        # Filter to Core Delivery only before cluster aggregation
        proc = _span_process_series(out_df)
        extract_family = detect_service_line_extract_family(out_df)
        sl_keys = span_service_line_keys_series(
            proc,
            out_df.get("DIVISION"),
            out_df.get("JOB_FUNCTION"),
            out_df.get("DESIGNATION"),
            out_df.get("ACCOUNT NAME"),
            out_df.get("COST CENTER"),
            extract_family,
        )
        core_mask = sl_keys.astype(str).isin(SPAN_SL_CORE_KEYS)
        out_df = out_df.loc[core_mask].copy()
        if out_df.empty:
            continue

        _, cluster_summary, _ = span_attach_cluster_and_summarize(out_df, cluster_mapping)
        if cluster_summary is None or cluster_summary.empty:
            # Fallback: single aggregate row
            agg_df = out_df.drop_duplicates(subset=["EMPLOYEE ID"], keep="first") if "EMPLOYEE ID" in out_df.columns else out_df
            vc = agg_df["IC / TL / M1+"].value_counts()
            ic = int(vc.get("IC", 0))
            tl = int(vc.get("TL", 0))
            m1 = int(vc.get("M1+", 0))
            cluster_summary = pd.DataFrame([{"Cluster": "All (no cluster mapping)", "IC": ic, "TL": tl, "M1+": m1, "Total rows": ic + tl + m1}])

        t = cluster_summary.copy()
        t["month_short"] = snap["month_short"]
        t["snapshot_order"] = snap.get("snapshot_order", i)
        t["snapshot_date"] = pd.Timestamp(year=snap["year"], month=snap["month"], day=snap["day"])
        t["Span (IC÷TL)"] = np.where(t["TL"] > 0, t["IC"].astype(float) / t["TL"].astype(float), np.nan)
        pieces.append(t)

    if not pieces:
        return pd.DataFrame()
    return pd.concat(pieces, ignore_index=True)


# ── service line ──────────────────────────────────────────────────────────────

def _span_hrms_cell_blank(val) -> bool:
    if val is None:
        return True
    try:
        if pd.isna(val):
            return True
    except Exception:
        pass
    if isinstance(val, (int, float, np.integer, np.floating)) and not isinstance(val, bool):
        try:
            if float(val) == 0.0:
                return True
        except Exception:
            pass
    s = str(val).strip()
    if s == "":
        return True
    if re.fullmatch(r"0+(\.0+)?", s):
        return True
    low = s.lower().strip()
    if low in {"nan", "none", "null", "nat", "<na>"}:
        return True
    na_like = re.sub(r"[^a-z0-9]", "", low)
    if na_like in {"na", "notapplicable"}:
        return True
    return False


def _sl_norm(x) -> str:
    if _span_hrms_cell_blank(x):
        return ""
    return re.sub(r"\s+", " ", str(x).strip().lower())


def _sl_norm_process(x) -> str:
    """Normalize PROCESS for service line matching."""
    s = _sl_norm(x)
    if not s:
        return s
    s = re.sub(r"[\|\｜\uff5c\u00a6]", " | ", s)
    return re.sub(r"\s+", " ", s).strip()


def _sl_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    t = _sl_norm(text)
    return any(n in t for n in needles)


def _span_classify_cache_scalar_str(val) -> str:
    """Stable string for classify memo keys (blank → empty)."""
    if _span_hrms_cell_blank(val):
        return ""
    return str(val).replace("\xa0", " ")


def _span_classify_cache_cc_str(cost_center) -> str:
    if _span_hrms_cell_blank(cost_center):
        return ""
    return str(cost_center).replace("\xa0", " ").strip().upper()


def _span_classify_service_line_row(
    process, division, job_function, designation="", account_name="", cost_center="",
    extract_family: str = "raw_hrms",
) -> tuple[str, str]:
    return _span_classify_service_line_row_memo(
        _span_classify_cache_scalar_str(process),
        _span_classify_cache_scalar_str(division),
        _span_classify_cache_scalar_str(job_function),
        _span_classify_cache_scalar_str(designation),
        _span_classify_cache_scalar_str(account_name),
        _span_classify_cache_cc_str(cost_center),
        str(extract_family),
    )


@lru_cache(maxsize=262144)
def _span_classify_service_line_row_memo(
    process: str,
    division: str,
    job_function: str,
    designation: str,
    account_name: str,
    cost_center: str,
    extract_family: str,
) -> tuple[str, str]:
    p = _sl_norm_process(process)
    d = _sl_norm(division)
    jf = _sl_norm(job_function)
    des = _sl_norm(designation)
    acc = _sl_norm(account_name)
    cc = cost_center  # already normalized by _span_classify_cache_cc_str

    # Step 0: Delivery Support prefix
    if p.startswith("delivery assurance & practices - bpm"):
        if "quality" in p:
            return "ds_quality", "Delivery Support (prefix) → Quality"
        if "training" in p:
            return "ds_training", "Delivery Support (prefix) → Training"
        if "wfm" in p:
            return "ds_wfm", "Delivery Support (prefix) → WFM"
        return "ds_others", "Delivery Support (prefix) → Others"

    if p.startswith("digital - bpm |"):
        return "ds_others", "Base Step 0 → ds_others"

    if p == "delivery support - others":
        return "ds_others", "Explicit PROCESS → ds_others"

    # Blank PROCESS handling
    if _span_hrms_cell_blank(process):
        if cc in FORCE_UNCLASSIFIED_CC or acc in FORCE_UNCLASSIFIED_ACCOUNT:
            return "unclassified", "Blank PROCESS → forced unclassified"

        if cc in BLANK_PROCESS_TO_DS_OTHERS_CC or acc in BLANK_PROCESS_TO_DS_OTHERS_ACCOUNT:
            return "ds_others", "Blank PROCESS → ds_others override"

        if d in {
            "clm domestic bfsi", "clm domestic diversified", "customer service",
            "customer contact center generalist", "customer contact center training / coaching",
        }:
            if _sl_contains_any(designation, COLLECTIONS_DESIG_TOKENS):
                return "core_collections", "Blank PROCESS → collections-like designation"
            if _sl_contains_any(designation, BACKOFFICE_DESIG_TOKENS):
                if extract_family == "raw_hrms":
                    return "ds_others", "Blank PROCESS → back-office-like designation (raw HRMS)"
                return "core_fa_back_office", "Blank PROCESS → back-office-like designation"
            return "core_clm", "Blank PROCESS → CLM-family division default"

        if "f&a" in d or "f & a" in d or d == "accounting":
            if extract_family == "raw_hrms":
                return "ds_others", "Blank PROCESS → F&A/accounting division (raw HRMS)"
            return "core_fa_back_office", "Blank PROCESS → F&A/accounting division"

        if d == "collections":
            return "core_collections", "Blank PROCESS → collections division"

        if jf == "call center collections":
            return "core_collections", "Blank PROCESS → collections job function"

        if jf in {"customer contact center generalist", "customer service"} and d in {
            "clm domestic bfsi", "clm domestic diversified", "customer service",
            "customer contact center generalist", "customer contact center training / coaching",
        }:
            return "core_clm", "Blank PROCESS → CLM job function within CLM-family division"

        if jf == "customer contact center training / coaching":
            return "ds_training", "Blank PROCESS → training job function"

        return "unclassified", "Blank PROCESS → no rule hit"

    # PROCESS rules by family
    family = "sept_style" if extract_family == "sept_style" else "dec_style"

    # raw_hrms: exact back-office processes → F&A back office
    if extract_family == "raw_hrms" and p in CLM_BACKOFFICE_PROCESS:
        return "core_fa_back_office", "Raw HRMS → exact back-office PROCESS"

    if family == "sept_style":
        if p in CLM_BACKOFFICE_PROCESS:
            return "core_fa_back_office", "Sept-style → back office"
        if p in CLM_VOICE_PROCESS:
            return "core_clm", "Sept-style → clm"
        if p in COLLECTIONS_PROCESS:
            return "core_collections", "Sept-style → collections"
        if p.startswith("clm"):
            return "core_clm", "CLM (prefix fallback) → clm"
        if p.startswith("collections"):
            return "core_collections", "Collections (prefix fallback) → collections"
    else:
        if p in CLM_BACKOFFICE_PROCESS:
            if cc in DEC_CLM_BACKOFFICE_TO_COLLECTIONS_CC:
                return "core_collections", "Dec PROCESS+CC override → collections"
            if cc in DEC_CLM_BACKOFFICE_TO_BACKOFFICE_CC:
                return "core_fa_back_office", "Dec PROCESS+CC override → back office"
            if cc in DEC_CLM_TO_DS_OTHERS_CC:
                return "ds_others", "Dec PROCESS+CC override → ds_others"
            if cc in DEC_FORCE_UNCLASSIFIED_CC:
                return "unclassified", "Dec PROCESS+CC override → unclassified"
            return "core_fa_back_office", "Dec default CLM back-office process → back office"

        if p in COLLECTIONS_PROCESS:
            if cc in DEC_COLLECTIONS_TO_BACKOFFICE_CC:
                return "core_fa_back_office", "Dec PROCESS+CC override → back office"
            if cc in DEC_COLLECTIONS_TO_CLM_CC:
                return "core_clm", "Dec PROCESS+CC override → clm"
            return "core_collections", "Dec default collections process → collections"

        if p in CLM_VOICE_PROCESS:
            if cc in DEC_CLMVOICE_TO_COLLECTIONS_CC:
                return "core_collections", "Dec PROCESS+CC override → collections"
            if cc in DEC_CLM_TO_DS_OTHERS_CC:
                return "ds_others", "Dec PROCESS+CC override → ds_others"
            if cc in DEC_FORCE_UNCLASSIFIED_CC:
                return "unclassified", "Dec PROCESS+CC override → unclassified"
            return "core_clm", "Dec default clm voice process → clm"

        if p.startswith("clm"):
            return "core_clm", "CLM (prefix fallback) → clm"
        if p.startswith("collections"):
            return "core_collections", "Collections (prefix fallback) → collections"

    return "unclassified", f"unclassified (PROCESS did not match rules; normalized={p!r})"


def _span_service_line_key_from_row(
    process, division, job_function, designation="", account_name="", cost_center="",
    extract_family: str = "raw_hrms",
) -> str:
    return _span_classify_service_line_row(
        process, division, job_function, designation, account_name, cost_center, extract_family
    )[0]


def span_service_line_keys_series(
    process_series: pd.Series,
    division_series: pd.Series | None = None,
    job_function_series: pd.Series | None = None,
    designation_series: pd.Series | None = None,
    account_name_series: pd.Series | None = None,
    cost_center_series: pd.Series | None = None,
    extract_family: str = "raw_hrms",
) -> pd.Series:
    n = len(process_series)
    idx = process_series.index

    if division_series is None:
        division_series = pd.Series([""] * n, index=idx)
    if job_function_series is None:
        job_function_series = pd.Series([""] * n, index=idx)
    if designation_series is None:
        designation_series = pd.Series([""] * n, index=idx)
    if account_name_series is None:
        account_name_series = pd.Series([""] * n, index=idx)
    if cost_center_series is None:
        cost_center_series = pd.Series([""] * n, index=idx)

    division_series = division_series.reindex(idx).fillna("")
    job_function_series = job_function_series.reindex(idx).fillna("")
    designation_series = designation_series.reindex(idx).fillna("")
    account_name_series = account_name_series.reindex(idx).fillna("")
    cost_center_series = cost_center_series.reindex(idx).fillna("")

    p_arr = process_series.values
    d_arr = division_series.values
    jf_arr = job_function_series.values
    des_arr = designation_series.values
    acc_arr = account_name_series.values
    cc_arr = cost_center_series.values
    results = [
        _span_service_line_key_from_row(p_arr[j], d_arr[j], jf_arr[j], des_arr[j], acc_arr[j], cc_arr[j], extract_family)
        for j in range(len(idx))
    ]
    return pd.Series(results, index=idx)


def workbook_display_to_core(display_label: str) -> str:
    """Map workbook display bucket label to internal service line key used for Tab 3 core / DS filters."""
    d = str(display_label).strip()
    m = {
        "CLM": "core_clm",
        "CXM": "core_clm",
        "Collections": "core_collections",
        "Collections (FOS)": "core_collections",
        "Collections (CLM)": "core_collections",
        "Back office": "core_fa_back_office",
        "Back Office & F&A": "core_fa_back_office",
        "Delivery support - Quality": "ds_quality",
        "Delivery support - Training": "ds_training",
        "Delivery support - WFM": "ds_wfm",
        "Delivery support - Others": "ds_others",
        "Delivery support": "ds_others",
        "Support Function": "unclassified",
        "Sales": "unclassified",
        "Unclassified — review needed": "unclassified",
        "Manpower": "unclassified",
        "tech and digital": "unclassified",
        "EXM": "unclassified",
        "Pending": "unclassified",
        "0": "unclassified",
        "CX": "unclassified",
    }
    return m.get(d, "unclassified")


def _span_normalize_bu_value(bu_val) -> str:
    if bu_val is None:
        return ""
    try:
        if pd.isna(bu_val):
            return ""
    except Exception:
        pass
    return str(bu_val).strip().lower()


# ── population filters ────────────────────────────────────────────────────────

def filter_code_delivery_population(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to pivot-like population (Sept/Dec/raw_hrms families)."""
    out = df.copy()
    family = detect_service_line_extract_family(out)

    if family == "sept_style":
        out = out[out["UPDATED BUSINESS UNIT"].astype(str).str.strip().eq("Conneqt BPM")]
        out = out[_series_is_zero_or_blank(out["EXCLUSION"])]
        if "SEPARATIONS" in out.columns:
            out = out[_series_is_zero_or_blank(out["SEPARATIONS"])]
        return out

    if family == "dec_style":
        out = out[out["LEGAL EMPLOYER NAME"].astype(str).str.strip().eq("Digitide Solutions Limited")]
        out = out[out["BUSINESS UNIT"].astype(str).str.strip().eq("BPM - Practices & Ops")]
        if "MANPOWER" in out.columns:
            out = out[_series_is_zero_or_blank(out["MANPOWER"])]
        if "SEPARATIONS" in out.columns:
            out = out[_series_is_zero_or_blank(out["SEPARATIONS"])]
        return out

    # raw HRMS fallback
    if "BUSINESS" in out.columns:
        out = out[out["BUSINESS"].astype(str).str.strip().eq("BPM - Practices & Ops")]
    if "BUSINESS UNIT" in out.columns:
        bu = out["BUSINESS UNIT"].astype(str).str.strip()
        if bu.str.lower().eq("digitide solutions limited").any():
            out = out[bu.str.lower().eq("digitide solutions limited")]
    if "SEPARATIONS" in out.columns:
        out = out[_series_is_zero_or_blank(out["SEPARATIONS"])]
    return out


def filter_exact_back_office_on_current_population(df: pd.DataFrame) -> pd.DataFrame:
    """Exact F&A back office = rows whose PROCESS is one of the 3 back-office processes, on current population."""
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    proc = _span_process_series(out)
    proc_norm = proc.apply(_sl_norm_process)
    out = out[proc_norm.isin(JAN_BO_PROCESSES)].copy()
    if out.empty:
        return out
    span_normalize_hrms_ids(out)
    return out


def filter_fa_back_office_population(df: pd.DataFrame, extract_family: str) -> pd.DataFrame:
    """Filter to F&A back office exact population (three processes) by extract family."""
    if df is None or df.empty:
        return pd.DataFrame()
    out = df.copy()
    if extract_family == "dec_style":
        if "LEGAL EMPLOYER NAME" not in out.columns or "BUSINESS UNIT" not in out.columns:
            return pd.DataFrame()
        out = out[out["LEGAL EMPLOYER NAME"].astype(str).str.strip().eq("Digitide Solutions Limited")].copy()
        out = out[out["BUSINESS UNIT"].astype(str).str.strip().eq("BPM - Practices & Ops")].copy()
        if "MANPOWER" in out.columns:
            out = out[_series_is_zero_or_blank(out["MANPOWER"])].copy()
        if "SEPARATIONS" in out.columns:
            out = out[_series_is_zero_or_blank(out["SEPARATIONS"])].copy()
    elif extract_family == "sept_style":
        if "UPDATED BUSINESS UNIT" not in out.columns:
            return pd.DataFrame()
        out = out[out["UPDATED BUSINESS UNIT"].astype(str).str.strip().eq("Conneqt BPM")].copy()
        out = out[_series_is_zero_or_blank(out["EXCLUSION"])].copy()
        if "SEPARATIONS" in out.columns:
            out = out[_series_is_zero_or_blank(out["SEPARATIONS"])].copy()
    elif extract_family == "raw_hrms":
        if "BUSINESS UNIT" not in out.columns or "BUSINESS" not in out.columns:
            return pd.DataFrame()
        out = out[out["BUSINESS UNIT"].astype(str).str.strip().eq("Digitide Solutions Limited")].copy()
        out = out[out["BUSINESS"].astype(str).str.strip().eq("BPM - Practices & Ops")].copy()
    else:
        return pd.DataFrame()
    proc = _span_process_series(out)
    proc_norm = proc.apply(_sl_norm_process)
    out = out[proc_norm.isin(JAN_BO_PROCESSES)].copy()
    if out.empty:
        return out
    span_normalize_hrms_ids(out)
    return out


# ── service line wide table ───────────────────────────────────────────────────

def span_service_line_wide_table(
    snapshots: list[dict],
    bu_filter_norm: tuple[str, ...] = (),
    use_code_delivery_pivot_filter: bool = False,
    conneqt_only: bool = True,
) -> pd.DataFrame:
    """
    Wide table: Category, Service line, one col per month (employee row counts).
    conneqt_only=True (default): Conneqt Business Solution only.
    """
    month_order = [s["month_short"] for s in snapshots]
    counts_by_month: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}

    for snap in snapshots:
        month_short = snap["month_short"]
        if conneqt_only:
            span_df, _, _, _ = span_prepare_and_detect_unknown(snap["raw_df"])
        else:
            span_df, _, _, _ = span_prepare_and_detect_unknown_all_business_units(snap["raw_df"])
        if span_df.empty:
            continue

        if not conneqt_only and use_code_delivery_pivot_filter:
            span_df = filter_code_delivery_population(span_df)
            if span_df.empty:
                continue

        if not conneqt_only and bu_filter_norm and "BUSINESS UNIT" in span_df.columns:
            bu_norm = span_df["BUSINESS UNIT"].astype(str).map(_span_normalize_bu_value)
            span_df = span_df.loc[bu_norm.isin(set(bu_filter_norm))].copy()
            if span_df.empty:
                continue

        extract_family = detect_service_line_extract_family(span_df)
        proc = _span_process_series(span_df)
        div = span_df.get("DIVISION")
        jf = span_df.get("JOB_FUNCTION")
        des = span_df.get("DESIGNATION")
        acc = span_df.get("ACCOUNT NAME")
        cc = span_df.get("COST CENTER")
        keys = span_service_line_keys_series(proc, div, jf, des, acc, cc, extract_family)

        # F&A back office raw_hrms: use exact 3-process matching
        fa_bo_emp_ids: set[str] = set()
        if extract_family == "raw_hrms":
            if conneqt_only:
                fa_bo_df = filter_exact_back_office_on_current_population(span_df)
            else:
                fa_bo_df = filter_fa_back_office_population(span_df, extract_family)
            if not fa_bo_df.empty and "EMPLOYEE ID" in fa_bo_df.columns:
                fa_bo_emp_ids = set(fa_bo_df["EMPLOYEE ID"].astype(str).drop_duplicates().tolist())
                counts_by_month[month_short]["core_fa_back_office"] = len(fa_bo_emp_ids)

        tmp = pd.DataFrame(
            {"sl": keys.astype(str).values, "emp_id": span_df["EMPLOYEE ID"].values},
            index=span_df.index,
        )
        tmp = tmp.drop_duplicates(subset=["emp_id"], keep="first")
        if fa_bo_emp_ids:
            tmp = tmp[~tmp["emp_id"].astype(str).isin(fa_bo_emp_ids)]
        vc = tmp.groupby("sl", dropna=False).size()
        for k, v in vc.items():
            if extract_family == "raw_hrms" and k == "core_fa_back_office":
                continue
            counts_by_month[month_short][str(k)] = int(v)

    rows: list[list] = []
    for cat, slabel, ikey in SPAN_SERVICE_LINE_ROW_SPEC:
        if ikey is None:
            rlist: list = [cat, slabel]
            for m in month_order:
                rlist.append(sum(counts_by_month[m].get(k, 0) for k in SPAN_SL_CORE_KEYS))
        else:
            rlist = [cat, slabel]
            for m in month_order:
                rlist.append(int(counts_by_month[m].get(ikey, 0)))
        rows.append(rlist)

    cols = ["Category", "Service line", *month_order]
    out = pd.DataFrame(rows, columns=cols)
    if len(month_order) >= 2:
        first_m, last_m = month_order[0], month_order[-1]
        out[f"Δ ({first_m} → {last_m})"] = (
            pd.to_numeric(out[last_m], errors="coerce").fillna(0)
            - pd.to_numeric(out[first_m], errors="coerce").fillna(0)
        )
    return out


def span_service_line_span_and_role_counts(
    snapshots: list[dict],
    unknown_grade_choices: dict[str, str] | None = None,
    bu_filter_norm: tuple[str, ...] = (),
    use_code_delivery_pivot_filter: bool = False,
    cluster_mapping: pd.DataFrame | None = None,
    conneqt_only: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns (span_wide, role_wide).
    Span formulas:
    - Quality/WFM: (ICs of all Core Delivery) ÷ (ICs + TLs of Quality/WFM)
    - Training: (ICs of CLM) ÷ (ICs + TLs of Training)
    - Others: IC ÷ TL
    """
    unknown_grade_choices = unknown_grade_choices or {}
    month_order = [s["month_short"] for s in snapshots]
    ic_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}
    tl_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}
    m1_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}

    for snap in snapshots:
        month_short = snap["month_short"]
        mo = int(snap.get("month", 0))
        if conneqt_only:
            span_df, _, _, _ = span_prepare_and_detect_unknown(snap["raw_df"])
        else:
            span_df, _, _, _ = span_prepare_and_detect_unknown_all_business_units(snap["raw_df"])
        if span_df.empty:
            continue

        if not conneqt_only and use_code_delivery_pivot_filter:
            span_df = filter_code_delivery_population(span_df)
            if span_df.empty:
                continue

        if not conneqt_only and bu_filter_norm and "BUSINESS UNIT" in span_df.columns:
            bu_norm = span_df["BUSINESS UNIT"].astype(str).map(_span_normalize_bu_value)
            span_df = span_df.loc[bu_norm.isin(set(bu_filter_norm))].copy()
            if span_df.empty:
                continue

        extract_family = detect_service_line_extract_family(span_df)
        proc = _span_process_series(span_df)
        div = span_df.get("DIVISION")
        jf = span_df.get("JOB_FUNCTION")
        des = span_df.get("DESIGNATION")
        acc = span_df.get("ACCOUNT NAME")
        cc = span_df.get("COST CENTER")
        keys = span_service_line_keys_series(proc, div, jf, des, acc, cc, extract_family)

        # September extra TL phrases
        extra_sept: frozenset[str] | None = SEPTEMBER_TL_COLLECTIONS_CLM_PHRASES if mo == 9 else None
        extra_emp_ids: frozenset[str] | None = None
        meu_ids: frozenset[str] | None = None
        if extra_sept:
            sl_mask = keys.astype(str).isin(SEPTEMBER_TL_EXTRA_PHRASES_SL_KEYS)
            if sl_mask.any() and "EMPLOYEE ID" in span_df.columns:
                extra_emp_ids = frozenset(span_df.loc[sl_mask, "EMPLOYEE ID"].astype(str).unique())
            meu_ids = _span_emp_ids_for_clusters(span_df, cluster_mapping, SEPTEMBER_TL_EXTRA_PHRASES_CLUSTER_NAMES)
            extra_emp_ids = (extra_emp_ids or frozenset()) | meu_ids

        role_s = span_classify_ic_tl_m1(
            span_df,
            unknown_grade_to_rule=unknown_grade_choices,
            extra_tl_designation_phrases=extra_sept,
            extra_tl_employee_ids=extra_emp_ids,
            extra_tl_meu_exclusion_phrases=SEPTEMBER_MEU_NON_TL_DESIGNATIONS if (extra_sept and meu_ids) else None,
            extra_tl_meu_employee_ids=meu_ids if extra_sept else None,
        )
        if role_s.empty:
            continue
        role_s = role_s.reindex(span_df.index).fillna("M1+").astype(str)
        role_s = role_s.where(role_s.isin({"IC", "TL", "M1+"}), "M1+")

        # F&A back office raw_hrms alignment
        fa_bo_emp_ids: set[str] = set()
        if extract_family == "raw_hrms":
            if conneqt_only:
                fa_bo_df = filter_exact_back_office_on_current_population(span_df)
            else:
                fa_bo_df = filter_fa_back_office_population(span_df, extract_family)
            if not fa_bo_df.empty and "EMPLOYEE ID" in fa_bo_df.columns:
                fa_bo_emp_ids = set(fa_bo_df["EMPLOYEE ID"].astype(str).drop_duplicates().tolist())

        sl_arr = keys.astype(str).to_numpy(copy=False)
        if extract_family == "raw_hrms" and fa_bo_emp_ids and "EMPLOYEE ID" in span_df.columns:
            emp_raw = span_df["EMPLOYEE ID"].astype(str).to_numpy()
            in_bo = np.isin(emp_raw, np.array(list(fa_bo_emp_ids), dtype=object))
            sl_arr = np.where(in_bo, "core_fa_back_office", sl_arr)

        tmp = pd.DataFrame({"sl": sl_arr, "role": role_s.values}, index=span_df.index)
        if "EMPLOYEE ID" in span_df.columns:
            tmp["emp_id"] = span_df["EMPLOYEE ID"].values
            tmp = tmp.drop_duplicates(subset=["emp_id"], keep="first")
        vc = tmp.groupby(["sl", "role"], observed=False).size()
        for (slk, role), cnt in vc.items():
            c = int(cnt)
            if role == "IC":
                ic_by[month_short][slk] += c
            elif role == "TL":
                tl_by[month_short][slk] += c
            elif role == "M1+":
                m1_by[month_short][slk] += c

    def _sl_row_ic_tl_m1(ikey, m):
        if ikey is None:
            ic = sum(ic_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
            tl = sum(tl_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
            m1 = sum(m1_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
        else:
            ic = ic_by[m].get(ikey, 0)
            tl = tl_by[m].get(ikey, 0)
            m1 = m1_by[m].get(ikey, 0)
        return ic, tl, m1

    def _sl_row_span(ikey, m) -> float:
        ic, tl, m1 = _sl_row_ic_tl_m1(ikey, m)
        if ikey == "ds_quality":
            num = sum(ic_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
            denom = ic + tl
            return round(num / denom, 4) if denom > 0 else np.nan
        if ikey == "ds_wfm":
            num = sum(ic_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
            denom = ic + tl
            return round(num / denom, 4) if denom > 0 else np.nan
        if ikey == "ds_training":
            num = ic_by[m].get("core_clm", 0)
            denom = ic + tl
            return round(num / denom, 4) if denom > 0 else np.nan
        return round(ic / tl, 4) if tl > 0 else np.nan

    span_rows: list[list] = []
    role_rows: list[list] = []
    for cat, slabel, ikey in SPAN_SERVICE_LINE_ROW_SPEC:
        sr = [cat, slabel]
        rr = [cat, slabel]
        for m in month_order:
            ic, tl, m1 = _sl_row_ic_tl_m1(ikey, m)
            rr.extend([ic, tl, m1])
            sr.append(_sl_row_span(ikey, m))
        span_rows.append(sr)
        role_rows.append(rr)

    span_cols = ["Category", "Service line", *month_order]
    span_out = pd.DataFrame(span_rows, columns=span_cols)
    role_col_list = ["Category", "Service line"]
    for m in month_order:
        role_col_list.extend([f"{m}_IC", f"{m}_TL", f"{m}_M1+"])
    role_out = pd.DataFrame(role_rows, columns=role_col_list)

    if len(month_order) >= 2:
        first_m, last_m = month_order[0], month_order[-1]
        a = pd.to_numeric(span_out[first_m], errors="coerce")
        b = pd.to_numeric(span_out[last_m], errors="coerce")
        span_out[f"Δ span ({first_m} → {last_m})"] = b - a

    return span_out, role_out


# ── account-wise span ─────────────────────────────────────────────────────────

def span_account_wise_table(
    snapshots: list[dict],
    cluster_mapping: pd.DataFrame | None,
    acc_map: pd.DataFrame | None,
    date_filter: list[str] | None = None,
    sl_filter: list[str] | None = None,
    cluster_filter: list[str] | None = None,
    unknown_grade_choices: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Build account-wise table: one column group per snapshot date.
    Per date: IC, TL, M1+, Total rows, Span (IC÷TL). Rows = accounts.
    """
    if acc_map is None or acc_map.empty:
        return pd.DataFrame()

    unknown_grade_choices = unknown_grade_choices or {}
    date_set = frozenset(str(d).strip() for d in (date_filter or []))
    sl_set = frozenset(sl_filter) if sl_filter else None
    cluster_set = frozenset(c.strip().lower() for c in (cluster_filter or [])) if cluster_filter else None

    from collections import defaultdict
    agg_triple: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0])
    months_with_data: set[str] = set()

    for snap in snapshots:
        ms = str(snap["month_short"]).strip()
        if date_set and ms not in date_set:
            continue
        mo = int(snap.get("month", 0))
        span_df, rc, _, _ = span_prepare_and_detect_unknown(snap["raw_df"])
        if span_df.empty:
            continue

        span_df = span_df.copy()
        span_df["_cc_key"] = span_df["COST CENTER"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""}) if "COST CENTER" in span_df.columns else ""

        merged = span_df.merge(acc_map, left_on="_cc_key", right_on="cc_key", how="left")
        merged["Account"] = merged["Account"].fillna("").astype(str).str.strip()
        merged["Cluster"] = merged["Cluster"].fillna("Unmapped").astype(str).str.strip()
        merged.loc[merged["Account"].eq(""), "Account"] = "— (no customer name in mapping)"
        merged.drop(columns=["_cc_key", "cc_key"], errors="ignore", inplace=True)

        extract_family = detect_service_line_extract_family(span_df)
        proc = _span_process_series(span_df)
        sl_keys = span_service_line_keys_series(
            proc, span_df.get("DIVISION"), span_df.get("JOB_FUNCTION"),
            span_df.get("DESIGNATION"), span_df.get("ACCOUNT NAME"), span_df.get("COST CENTER"), extract_family,
        )

        extra_sept: frozenset[str] | None = SEPTEMBER_TL_COLLECTIONS_CLM_PHRASES if mo == 9 else None
        extra_emp_ids: frozenset[str] | None = None
        meu_ids: frozenset[str] | None = None
        if extra_sept and "EMPLOYEE ID" in span_df.columns:
            sl_mask = sl_keys.astype(str).isin(SEPTEMBER_TL_EXTRA_PHRASES_SL_KEYS)
            if sl_mask.any():
                extra_emp_ids = frozenset(span_df.loc[sl_mask, "EMPLOYEE ID"].astype(str).unique())
            meu_ids = _span_emp_ids_for_clusters(span_df, cluster_mapping, SEPTEMBER_TL_EXTRA_PHRASES_CLUSTER_NAMES)
            extra_emp_ids = (extra_emp_ids or frozenset()) | meu_ids

        role_s = span_classify_ic_tl_m1(
            span_df, rc,
            unknown_grade_to_rule=unknown_grade_choices,
            extra_tl_designation_phrases=extra_sept,
            extra_tl_employee_ids=extra_emp_ids,
            extra_tl_meu_exclusion_phrases=SEPTEMBER_MEU_NON_TL_DESIGNATIONS if (extra_sept and meu_ids) else None,
            extra_tl_meu_employee_ids=meu_ids if extra_sept else None,
        )
        if role_s.empty or len(role_s) != len(span_df):
            continue

        merged["_sl_key"] = sl_keys.values
        merged["_role"] = role_s.values
        merged["_icl"] = (merged["_role"] == "IC").astype(int)
        merged["_tll"] = (merged["_role"] == "TL").astype(int)
        merged["_m1l"] = (merged["_role"] == "M1+").astype(int)

        if sl_set is not None:
            merged = merged[merged["_sl_key"].astype(str).isin(sl_set)]
        if cluster_set is not None:
            merged = merged[merged["Cluster"].str.strip().str.lower().isin(cluster_set)]

        if "EMPLOYEE ID" in merged.columns:
            merged = merged.drop_duplicates(subset=["EMPLOYEE ID"], keep="first")

        if merged.empty:
            continue
        months_with_data.add(ms)

        for acc_name, grp in merged.groupby("Account", dropna=False):
            an = str(acc_name).strip() if pd.notna(acc_name) else "— (no customer name in mapping)"
            t = agg_triple[(an, ms)]
            t[0] += int(grp["_icl"].sum())
            t[1] += int(grp["_tll"].sum())
            t[2] += int(grp["_m1l"].sum())

    if not months_with_data:
        return pd.DataFrame()

    date_order = sorted(months_with_data)
    all_acc = sorted({k[0] for k in agg_triple.keys()})
    rows: list[dict] = []
    for acc_name in all_acc:
        row: dict = {"Account name": acc_name}
        for ms in date_order:
            ic, tl, m1 = agg_triple.get((acc_name, ms), [0, 0, 0])
            tot = ic + tl + m1
            pfx = ms.replace(":", " ").strip()
            row[f"{pfx} | IC"] = ic
            row[f"{pfx} | TL"] = tl
            row[f"{pfx} | M1+"] = m1
            row[f"{pfx} | Total rows"] = tot
            row[f"{pfx} | Span (IC÷TL)"] = round(ic / tl, 2) if tl > 0 else None
        rows.append(row)

    return pd.DataFrame(rows)


def span_account_wise_tree(
    snapshots: list[dict],
    cluster_mapping: pd.DataFrame | None,
    acc_map: pd.DataFrame | None,
    date_filter: list[str] | None = None,
    sl_filter: list[str] | None = None,
    cluster_filter: list[str] | None = None,
    unknown_grade_choices: dict[str, str] | None = None,
) -> list[dict]:
    """
    Build account-wise span tree: Account → Cluster → Service line with dates as columns.
    Returns list of dicts for JSON serialization.
    """
    _SL_KEY_TO_LABEL = {
        "core_collections": "Collections",
        "core_clm": "CLM",
        "core_fa_back_office": "F&A & back office",
    }

    if acc_map is None or acc_map.empty:
        return []

    unknown_grade_choices = unknown_grade_choices or {}
    date_set = frozenset(str(d).strip() for d in (date_filter or []))
    sl_set = frozenset(sl_filter) if sl_filter else None
    cluster_set = frozenset(c.strip().lower() for c in (cluster_filter or [])) if cluster_filter else None

    from collections import defaultdict
    agg: dict[tuple[str, str, str, str], tuple[int, int]] = defaultdict(lambda: (0, 0))
    date_labels: set[str] = set()

    for snap in snapshots:
        ms = str(snap["month_short"]).strip()
        if date_set and ms not in date_set:
            continue
        mo = int(snap.get("month", 0))
        span_df, rc, _, _ = span_prepare_and_detect_unknown(snap["raw_df"])
        if span_df.empty:
            continue

        span_df = span_df.copy()
        cc_col = span_df["COST CENTER"].astype(str).str.strip().str.upper().replace({"NAN": "", "NONE": ""}) if "COST CENTER" in span_df.columns else pd.Series([""] * len(span_df), index=span_df.index)
        span_df["_cc_key"] = cc_col

        merged = span_df.merge(acc_map, left_on="_cc_key", right_on="cc_key", how="left")
        merged["Account"] = merged["Account"].fillna("").astype(str).str.strip()
        merged["Cluster"] = merged["Cluster"].fillna("Unmapped").astype(str).str.strip()
        merged.loc[merged["Account"].eq(""), "Account"] = "— (no customer name in mapping)"
        merged.drop(columns=["_cc_key", "cc_key"], errors="ignore", inplace=True)

        extract_family = detect_service_line_extract_family(span_df)
        proc = _span_process_series(span_df)
        sl_keys = span_service_line_keys_series(
            proc, span_df.get("DIVISION"), span_df.get("JOB_FUNCTION"),
            span_df.get("DESIGNATION"), span_df.get("ACCOUNT NAME"), span_df.get("COST CENTER"), extract_family,
        )

        extra_sept: frozenset[str] | None = SEPTEMBER_TL_COLLECTIONS_CLM_PHRASES if mo == 9 else None
        extra_emp_ids: frozenset[str] | None = None
        meu_ids: frozenset[str] | None = None
        if extra_sept and "EMPLOYEE ID" in span_df.columns:
            sl_mask = sl_keys.astype(str).isin(SEPTEMBER_TL_EXTRA_PHRASES_SL_KEYS)
            if sl_mask.any():
                extra_emp_ids = frozenset(span_df.loc[sl_mask, "EMPLOYEE ID"].astype(str).unique())
            meu_ids = _span_emp_ids_for_clusters(span_df, cluster_mapping, SEPTEMBER_TL_EXTRA_PHRASES_CLUSTER_NAMES)
            extra_emp_ids = (extra_emp_ids or frozenset()) | meu_ids

        role_s = span_classify_ic_tl_m1(
            span_df, rc,
            unknown_grade_to_rule=unknown_grade_choices,
            extra_tl_designation_phrases=extra_sept,
            extra_tl_employee_ids=extra_emp_ids,
            extra_tl_meu_exclusion_phrases=SEPTEMBER_MEU_NON_TL_DESIGNATIONS if (extra_sept and meu_ids) else None,
            extra_tl_meu_employee_ids=meu_ids if extra_sept else None,
        )
        if role_s.empty or len(role_s) != len(span_df):
            continue

        merged["_sl_key"] = sl_keys.values
        merged["_role"] = role_s.values
        merged["_icl"] = (merged["_role"] == "IC").astype(int)
        merged["_tll"] = (merged["_role"] == "TL").astype(int)

        if sl_set is not None:
            merged = merged[merged["_sl_key"].astype(str).isin(sl_set)]
        if cluster_set is not None:
            merged = merged[merged["Cluster"].str.strip().str.lower().isin(cluster_set)]

        if "EMPLOYEE ID" in merged.columns:
            merged = merged.drop_duplicates(subset=["EMPLOYEE ID"], keep="first")

        for (acc_name, cluster, slk), grp in merged.groupby(["Account", "Cluster", "_sl_key"], dropna=False):
            an = str(acc_name).strip() if pd.notna(acc_name) else "—"
            cl = str(cluster).strip() if pd.notna(cluster) else "—"
            sl = str(slk).strip() if pd.notna(slk) else "—"
            key = (an, cl, sl, ms)
            prev_ic, prev_tl = agg[key]
            agg[key] = (prev_ic + int(grp["_icl"].sum()), prev_tl + int(grp["_tll"].sum()))
            date_labels.add(ms)

    if not agg:
        return []

    date_order = sorted(date_labels)

    # Build tree rows
    rows: list[dict] = []
    for (acc, cluster, sl_key, month), (ic, tl) in agg.items():
        sl_label = _SL_KEY_TO_LABEL.get(sl_key, sl_key)
        span_val = round(ic / tl, 2) if tl > 0 else None
        rows.append({
            "account": acc,
            "cluster": cluster,
            "service_line": sl_label,
            "month_short": month,
            "IC": ic,
            "TL": tl,
            "span": span_val,
        })

    return rows
