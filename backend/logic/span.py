import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

from logic.constants import (
    BUCKET_CONNEQT, SPAN_TL_DESIGNATIONS,
    SPAN_SL_CORE_KEYS, SPAN_SERVICE_LINE_ROW_SPEC, _SPAN_SERVICE_LINE_RULES_VERSION,
    SPAN_SL_CC_OVERRIDE, DIVISION_CLM_WHEN_PROCESS_BLANK,
    COLLECTIONS_DESIG_TOKENS, BACKOFFICE_DESIG_TOKENS,
    DS_OTHERS_DESIG_TOKENS, CLM_GENERIC_DESIG_TOKENS,
)
from logic.normalization import normalize_hr_cols, normalize_span_hrms_cols
from logic.bucketing import classify_bucket_type1, classify_bucket_type2, _detect_file_type_from_normalized
from logic.utils import span_normalize_hrms_ids


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


def _span_designation_normalized(des_series: pd.Series) -> pd.Series:
    return des_series.astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True).fillna("")


def _span_mandatory_tl_designation_match(des_norm_lower: pd.Series) -> pd.Series:
    phrases = tuple(p.strip().lower() for p in SPAN_TL_DESIGNATIONS if str(p).strip())
    if not phrases:
        return pd.Series(False, index=des_norm_lower.index)
    des_compact = des_norm_lower.astype(str).str.replace(r"\s+", "", regex=True)
    out = pd.Series(False, index=des_norm_lower.index)
    for p in phrases:
        p_compact = re.sub(r"\s+", "", p)
        if not p_compact:
            continue
        out = out | des_compact.str.contains(re.escape(p_compact), regex=True, na=False)
    return out


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


# ── prepare & detect unknown ─────────────────────────────────────────────────

def _apply_manpower_exclusion(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "PROCESS" in df.columns:
        exclude_mp = _span_series_process_contains_manpower(df["PROCESS"])
        return df.loc[~exclude_mp].copy()
    elif "MANPOWER CHECK" in df.columns:
        mc = df["MANPOWER CHECK"]
        num = pd.to_numeric(mc, errors="coerce")
        exclude_mp = (num == 1) | (mc.astype(str).str.strip() == "1")
        return df.loc[~exclude_mp].copy()
    return df


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
    conneqt_df = _apply_manpower_exclusion(conneqt_df)

    if conneqt_df.empty:
        return conneqt_df, pd.Series(dtype=int), set(), set()

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
    span_df = _apply_manpower_exclusion(span_df)

    if span_df.empty:
        return span_df, pd.Series(dtype=int), set(), set()

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
    grades_raw_row = grade_src.astype(str).fillna("").map(lambda x: str(x).strip())
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
    has_tl_desig = _span_mandatory_tl_designation_match(des_l)
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
    from logic.utils import keyify

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
            from logic.utils import keyify
            if keyify(str(c)) == "cluster":
                cluster_col = c
                break
    if cluster_col is None:
        from logic.utils import keyify
        col_map = {keyify(c): c for c in df.columns if not str(c).lower().startswith("unnamed")}
        for alias in ("vertical", "cluster name", "business cluster"):
            if alias in col_map:
                cluster_col = col_map[alias]
                break
    return code_col, cluster_col


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
    last_cols = []
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
    out = out.merge(cluster_mapping, left_on="_cc_key", right_on="cc_key", how="left", suffixes=("", "_map"))
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

    pv = (
        out.groupby(["Cluster", role_col], dropna=False)
        .size()
        .unstack(fill_value=0)
        .reindex(columns=["IC", "TL", "M1+"], fill_value=0)
    )
    pv["Total rows"] = pv.sum(axis=1)
    pv = pv.reset_index()
    pv["_u"] = pv["Cluster"].eq("Unmapped")
    pv = pv.sort_values(["_u", "Cluster"]).drop(columns=["_u"])
    return out, pv, " ".join(msg_parts)


# ── trend by cluster ──────────────────────────────────────────────────────────

def span_trend_ic_tl_by_cluster(
    snapshots: list[dict],
    cluster_mapping: pd.DataFrame | None,
    unknown_grade_choices: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    snapshots: list of dicts with keys: raw_df, month_short, year, month, day, snapshot_order
    Returns long-format DataFrame with one row per (snapshot, Cluster).
    """
    unknown_grade_choices = unknown_grade_choices or {}
    pieces: list[pd.DataFrame] = []

    for i, snap in enumerate(snapshots):
        raw_df = snap["raw_df"]
        conneqt_df, rc, _, _ = span_prepare_and_detect_unknown(raw_df)
        if conneqt_df.empty:
            continue
        role_s = span_classify_ic_tl_m1(conneqt_df, rc, unknown_grade_to_rule=unknown_grade_choices)
        if role_s.empty or len(role_s) != len(conneqt_df):
            continue
        out_df = conneqt_df.copy()
        out_df["IC / TL / M1+"] = role_s.values
        _, cluster_summary, _ = span_attach_cluster_and_summarize(out_df, cluster_mapping)
        if cluster_summary is None or cluster_summary.empty:
            continue
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


def _sl_contains_any(text: str, needles: tuple[str, ...]) -> bool:
    t = _sl_norm(text)
    return any(n in t for n in needles)


def _span_classify_service_line_row(
    process, division, job_function, designation="", account_name="", cost_center=""
) -> tuple[str, str]:
    _ = account_name
    p = _sl_norm(process)
    d = _sl_norm(division)
    jf = _sl_norm(job_function)
    cc = "" if _span_hrms_cell_blank(cost_center) else str(cost_center).strip().upper()

    if cc in SPAN_SL_CC_OVERRIDE:
        k = SPAN_SL_CC_OVERRIDE[cc]
        return k, f"CC override → {k} (cc={cc!r})"

    if _span_hrms_cell_blank(process):
        if d in DIVISION_CLM_WHEN_PROCESS_BLANK:
            if _sl_contains_any(designation, COLLECTIONS_DESIG_TOKENS):
                return "core_collections", "Blank PROCESS + Division override → core_collections"
            if _sl_contains_any(designation, BACKOFFICE_DESIG_TOKENS):
                return "core_fa_back_office", "Blank PROCESS + Division override → core_fa_back_office"
            if _sl_contains_any(designation, DS_OTHERS_DESIG_TOKENS):
                return "ds_others", "Blank PROCESS + Division override → ds_others"
            return "core_clm", "Blank PROCESS + Division override → core_clm"
        if "f&a" in d or "f & a" in d:
            return "core_fa_back_office", "Base Step 2 → core_fa_back_office (F&A in division)"
        if d == "collections":
            return "core_collections", "Base Step 2 → core_collections (division equals collections)"
        if jf == "call center collections":
            return "core_collections", "Base Step 3 → core_collections (JOB_FUNCTION)"
        if jf in {"customer contact center generalist", "customer service"}:
            return "core_clm", "Base Step 3 → core_clm (JOB_FUNCTION)"
        if jf == "customer contact center training / coaching":
            return "ds_training", "Base Step 3 → ds_training (JOB_FUNCTION)"
        return "unclassified", "unclassified (blank PROCESS; no division/JOB_FUNCTION match)"

    if p.startswith("delivery assurance & practices - bpm |"):
        if "quality" in p:
            return "ds_quality", "Base Step 1 → ds_quality"
        if "training" in p:
            return "ds_training", "Base Step 1 → ds_training"
        if "wfm" in p:
            return "ds_wfm", "Base Step 1 → ds_wfm"
        return "ds_others", "Base Step 1 → ds_others"

    if p.startswith("digital - bpm |"):
        return "ds_others", "Base Step 1 → ds_others (digital - bpm)"

    if p in {
        "clm domestic bfsi | back office",
        "clm domestic diversified | back office",
        "clm international | back office",
    }:
        return "core_clm", "Process override → core_clm (CLM | back office remap)"

    if p in {"collections | fos", "collections | telecollection"}:
        if _sl_contains_any(designation, CLM_GENERIC_DESIG_TOKENS) and not _sl_contains_any(
            designation, COLLECTIONS_DESIG_TOKENS
        ):
            return "core_clm", "Process override → core_clm (Collections | FOS/Tele + generic CLM designation)"
        return "core_collections", "Process override → core_collections (Collections | FOS/Tele)"

    if p in {
        "clm domestic bfsi | inbound", "clm domestic bfsi | outbound",
        "clm domestic diversified | inbound", "clm domestic diversified | outbound",
        "clm international | inbound", "clm international | outbound",
    }:
        return "core_clm", "Base Step 1 → core_clm (CLM inbound/outbound)"

    if p in {"collections", "collections | fos", "collections | telecollection"}:
        return "core_collections", "Base Step 1 → core_collections"

    return "unclassified", f"unclassified (PROCESS did not match rules; normalized={p!r})"


def span_service_line_keys_series(
    process_series: pd.Series,
    division_series: pd.Series | None = None,
    job_function_series: pd.Series | None = None,
    designation_series: pd.Series | None = None,
    account_name_series: pd.Series | None = None,
    cost_center_series: pd.Series | None = None,
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

    for s in (division_series, job_function_series, designation_series, account_name_series, cost_center_series):
        s = s.reindex(idx)

    out = pd.Series(index=idx, dtype=object)
    for i in idx:
        out.loc[i] = _span_classify_service_line_row(
            process_series.loc[i],
            division_series.loc[i],
            job_function_series.loc[i],
            designation_series.loc[i],
            account_name_series.loc[i],
            cost_center_series.loc[i],
        )[0]
    return out


def _span_normalize_bu_value(bu_val) -> str:
    if bu_val is None:
        return ""
    try:
        if pd.isna(bu_val):
            return ""
    except Exception:
        pass
    return str(bu_val).strip().lower()


def filter_code_delivery_population(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "LEGAL EMPLOYER NAME" in out.columns:
        out = out[out["LEGAL EMPLOYER NAME"].astype(str).str.strip().eq("Digitide Solutions Limited")]
    if "BUSINESS UNIT" in out.columns:
        out = out[out["BUSINESS UNIT"].astype(str).str.strip().eq("BPM - Practices & Ops")]
    if "SEPARATIONS" in out.columns:
        def _sep_active(x) -> bool:
            if _span_hrms_cell_blank(x):
                return True
            return str(x).strip().lower() in {"0", "0.0"}
        out = out[out["SEPARATIONS"].map(_sep_active)]
    if "MANPOWER" in out.columns:
        out = out[out["MANPOWER"].map(_span_hrms_cell_blank)]
    return out


def span_service_line_wide_table(
    snapshots: list[dict],
    bu_filter_norm: tuple[str, ...] = (),
    use_code_delivery_pivot_filter: bool = False,
) -> pd.DataFrame:
    """
    snapshots: list of dicts with raw_df, month_short
    Returns wide table: Category, Service line, one col per month.
    """
    month_order = [s["month_short"] for s in snapshots]
    counts_by_month: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}

    for snap in snapshots:
        month_short = snap["month_short"]
        span_df, _, _, _ = span_prepare_and_detect_unknown_all_business_units(snap["raw_df"])
        if span_df.empty:
            continue
        if bu_filter_norm and "BUSINESS UNIT" in span_df.columns:
            bu_norm = span_df["BUSINESS UNIT"].astype(str).map(_span_normalize_bu_value)
            span_df = span_df.loc[bu_norm.isin(set(bu_filter_norm))].copy()
            if span_df.empty:
                continue
        if use_code_delivery_pivot_filter:
            span_df = filter_code_delivery_population(span_df)
            if span_df.empty:
                continue

        proc = span_df["PROCESS"] if "PROCESS" in span_df.columns else pd.Series([""] * len(span_df), index=span_df.index)
        div = span_df.get("DIVISION")
        jf = span_df.get("JOB_FUNCTION")
        des = span_df.get("DESIGNATION")
        acc = span_df.get("ACCOUNT NAME")
        cc = span_df.get("COST CENTER")
        keys = span_service_line_keys_series(proc, div, jf, des, acc, cc)
        for k, v in keys.value_counts().items():
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
) -> tuple[pd.DataFrame, pd.DataFrame]:
    unknown_grade_choices = unknown_grade_choices or {}
    month_order = [s["month_short"] for s in snapshots]
    ic_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}
    tl_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}
    m1_by: dict[str, dict[str, int]] = {m: defaultdict(int) for m in month_order}

    for snap in snapshots:
        month_short = snap["month_short"]
        span_df, _, _, _ = span_prepare_and_detect_unknown_all_business_units(snap["raw_df"])
        if span_df.empty:
            continue
        if bu_filter_norm and "BUSINESS UNIT" in span_df.columns:
            bu_norm = span_df["BUSINESS UNIT"].astype(str).map(_span_normalize_bu_value)
            span_df = span_df.loc[bu_norm.isin(set(bu_filter_norm))].copy()
            if span_df.empty:
                continue
        if use_code_delivery_pivot_filter:
            span_df = filter_code_delivery_population(span_df)
            if span_df.empty:
                continue

        role_s = span_classify_ic_tl_m1(span_df, unknown_grade_to_rule=unknown_grade_choices)
        if role_s.empty:
            continue

        proc = span_df["PROCESS"] if "PROCESS" in span_df.columns else pd.Series([""] * len(span_df), index=span_df.index)
        div = span_df.get("DIVISION")
        jf = span_df.get("JOB_FUNCTION")
        des = span_df.get("DESIGNATION")
        acc = span_df.get("ACCOUNT NAME")
        cc = span_df.get("COST CENTER")
        keys = span_service_line_keys_series(proc, div, jf, des, acc, cc)
        tmp = pd.DataFrame(
            {"sl": keys.astype(str).values, "role": role_s.reindex(span_df.index).astype(str).values},
            index=span_df.index,
        )
        vc = tmp.groupby(["sl", "role"], observed=False).size()
        for (slk, role), cnt in vc.items():
            c = int(cnt)
            if role == "IC":
                ic_by[month_short][slk] += c
            elif role == "TL":
                tl_by[month_short][slk] += c
            elif role == "M1+":
                m1_by[month_short][slk] += c

    def _sl_row(ikey, m):
        if ikey is None:
            ic = sum(ic_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
            tl = sum(tl_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
            m1 = sum(m1_by[m].get(k, 0) for k in SPAN_SL_CORE_KEYS)
        else:
            ic, tl, m1 = ic_by[m].get(ikey, 0), tl_by[m].get(ikey, 0), m1_by[m].get(ikey, 0)
        return ic, tl, m1

    span_rows: list[list] = []
    role_rows: list[list] = []
    for cat, slabel, ikey in SPAN_SERVICE_LINE_ROW_SPEC:
        sr = [cat, slabel]
        rr = [cat, slabel]
        for m in month_order:
            ic, tl, m1 = _sl_row(ikey, m)
            rr.extend([ic, tl, m1])
            sr.append(round(ic / tl, 4) if tl > 0 else np.nan)
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
