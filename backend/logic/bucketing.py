import pandas as pd

from logic.constants import (
    BUCKET_ALLDIGI, BUCKET_CXO, BUCKET_CONNEQT, BUCKET_TECHDIG,
    BPM_BUSINESS, VERTICAL_BUSINESS, TECH_DIGITAL_BUSINESS, HR_BUSINESS,
    SUPPORT_PREFIX, CXO_CODES_TYPE2, ADMIN_BUCKET_VARIANTS_TO_COLLAPSE,
)
from logic.utils import clean_text_series
from logic.normalization import normalize_hr_cols


def normalize_support_buckets(bucket: pd.Series) -> pd.Series:
    out = bucket.copy()
    bucket_lower = out.str.strip().str.lower()
    admin_mask = bucket_lower.isin(ADMIN_BUCKET_VARIANTS_TO_COLLAPSE)
    out = out.mask(admin_mask, "Support Functions - Admin")
    strategy_ai_mask = bucket_lower.isin({
        "support functions - strategy",
        "support functions - ai",
        "support functions - strategy and ai",
    })
    out = out.mask(strategy_ai_mask, "Support Functions - Strategy & AI")
    return out


def classify_bucket_type1(df: pd.DataFrame) -> pd.Series:
    business_l = clean_text_series(df["BUSINESS"]).fillna("").str.lower().str.strip()
    bu_raw = clean_text_series(df["BUSINESS UNIT"]).fillna("")
    bu_l = bu_raw.str.lower().str.strip()

    is_conneqt = bu_l.eq("conneqt business solution")
    is_alldigi = business_l.eq(BPM_BUSINESS) & bu_l.str.contains("alldigi", na=False)
    is_techdig = bu_l.str.contains("tech & digital", na=False)
    is_cxo = bu_l.eq("cxo")

    is_support_bu = bu_l.str.startswith("support function -", na=False)
    support_suffix = bu_raw.str.replace("Support Function -", "", regex=False).str.strip()
    support_bucket_from_support = SUPPORT_PREFIX + support_suffix
    support_bucket_from_other = SUPPORT_PREFIX + bu_raw

    bucket = support_bucket_from_other
    bucket = bucket.mask(is_support_bu, support_bucket_from_support)
    bucket = bucket.mask(is_techdig, BUCKET_TECHDIG)
    bucket = bucket.mask(is_alldigi, BUCKET_ALLDIGI)
    bucket = bucket.mask(is_conneqt, BUCKET_CONNEQT)
    bucket = bucket.mask(is_cxo, BUCKET_CXO)

    return normalize_support_buckets(bucket)


def classify_bucket_type2(df: pd.DataFrame) -> pd.Series:
    business = clean_text_series(df["BUSINESS"]).fillna("")
    business_l = business.str.lower().str.strip()

    bu = clean_text_series(df["BUSINESS UNIT"]).fillna("")
    bu_l = bu.str.lower().str.strip()

    lvl_u = (
        clean_text_series(df["LEVEL"]).fillna("").str.upper().str.strip()
        if "LEVEL" in df.columns else pd.Series([""] * len(df), index=df.index)
    )
    des_u = (
        clean_text_series(df["DESIGNATION"]).fillna("").str.upper().str.strip()
        if "DESIGNATION" in df.columns else pd.Series([""] * len(df), index=df.index)
    )
    grd_u = (
        clean_text_series(df["GRADE"]).fillna("").str.upper().str.strip()
        if "GRADE" in df.columns else pd.Series([""] * len(df), index=df.index)
    )

    cxo_tokens = set(CXO_CODES_TYPE2) | {"CEO"}
    is_cxo = lvl_u.isin(cxo_tokens) | des_u.isin(cxo_tokens) | grd_u.isin(cxo_tokens)

    bucket = SUPPORT_PREFIX + business

    is_techdig = business_l.isin(TECH_DIGITAL_BUSINESS)
    is_alldigi = business_l.eq(BPM_BUSINESS) & bu_l.str.contains("alldigi", na=False)
    is_conneqt = business_l.isin({BPM_BUSINESS, VERTICAL_BUSINESS}) & bu_l.eq("digitide solutions limited")

    bucket = bucket.mask(is_techdig, BUCKET_TECHDIG)
    bucket = bucket.mask(is_alldigi, BUCKET_ALLDIGI)
    bucket = bucket.mask(is_conneqt, BUCKET_CONNEQT)
    bucket = bucket.mask(is_cxo, BUCKET_CXO)

    is_hr = business_l.isin(HR_BUSINESS)
    bucket = bucket.mask(
        is_hr & (~bucket.isin([BUCKET_CONNEQT, BUCKET_ALLDIGI, BUCKET_TECHDIG, BUCKET_CXO])),
        SUPPORT_PREFIX + "HR",
    )
    return normalize_support_buckets(bucket)


def _detect_file_type_from_normalized(d: pd.DataFrame) -> str:
    if "BUSINESS UNIT" not in d.columns:
        return "type2"
    bu = clean_text_series(d["BUSINESS UNIT"]).fillna("").str.lower().str.strip()
    c_conneqt = int((bu == "conneqt business solution").sum())
    c_digitide = int((bu == "digitide solutions limited").sum())
    if c_conneqt >= 10:
        return "type1"
    if c_digitide >= 10:
        return "type2"
    return "type2"


def detect_file_type(df_raw: pd.DataFrame) -> str:
    d = normalize_hr_cols(df_raw)
    return _detect_file_type_from_normalized(d)
