from __future__ import annotations
import re
from pathlib import Path

import pandas as pd

from logic.constants import HR_MANDATORY_STD, HR_FILE_RE
from logic.utils import (
    to_id_string, clean_text_series, read_excel_best_sheet, format_snapshot_date,
    normalize_otc_pa_to_cr,
)
from logic.normalization import normalize_hr_cols
from logic.bucketing import _detect_file_type_from_normalized, classify_bucket_type1, classify_bucket_type2
from logic.utils import ensure_cols


def prepare_hr_snapshot(df_raw: pd.DataFrame, *, is_previous: bool) -> tuple[pd.DataFrame, pd.Series, str]:
    df = normalize_hr_cols(df_raw)
    file_type = _detect_file_type_from_normalized(df)
    ensure_cols(df, HR_MANDATORY_STD, "Previous HR" if is_previous else "Current HR")

    if "SEPARATION" in df.columns:
        sep_raw = clean_text_series(df["SEPARATION"]).fillna("").astype(str).str.strip().str.lower()
        sep_num = pd.to_numeric(sep_raw, errors="coerce")
        is_one = (sep_num.eq(1) | sep_raw.eq("1")).fillna(False)
        df = df[~is_one].copy()

    df["BUSINESS UNIT"] = clean_text_series(df["BUSINESS UNIT"])
    df = df[df["BUSINESS UNIT"].notna()].copy()

    if "EMPLOYEE TYPE" in df.columns:
        emp_type = df["EMPLOYEE TYPE"].astype(str).str.strip().str.upper()
        df = df[emp_type.isin({"C", "E"})].copy()

    df["EMPLOYEE ID"] = df["EMPLOYEE ID"].map(to_id_string)
    df = df[df["EMPLOYEE ID"].notna()].copy()

    df["BUSINESS"] = clean_text_series(df["BUSINESS"]).fillna("")
    df = df.drop_duplicates(subset=["EMPLOYEE ID"], keep="first").copy()

    if file_type == "type1":
        df["BUCKET"] = classify_bucket_type1(df)
    else:
        df["BUCKET"] = classify_bucket_type2(df)

    if "OTC PA" in df.columns:
        df["OTC PA (CR)"] = normalize_otc_pa_to_cr(df["OTC PA"])
    else:
        import numpy as np
        df["OTC PA (CR)"] = np.nan

    counts = df.groupby("BUCKET")["EMPLOYEE ID"].nunique()
    return df, counts, file_type


def load_snapshot(file_bytes: bytes, is_previous: bool) -> tuple[pd.DataFrame, pd.Series, str, pd.DataFrame]:
    """Load from raw bytes (uploaded file). Returns (df, counts, file_type, raw_df)."""
    import io
    raw = read_excel_best_sheet(io.BytesIO(file_bytes))
    raw_clean = raw.dropna(how="all")
    df, counts, file_type = prepare_hr_snapshot(raw_clean, is_previous=is_previous)
    return df, counts, file_type, raw_clean


def _hr_folder_skip_non_snapshot_xlsx(filename: str) -> bool:
    low = filename.lower()
    if low.startswith("~$"):
        return True
    if "conneqt" in low and "cost" in low and "mapp" in low:
        return True
    if "costcode" in low.replace(" ", "") and "mapp" in low:
        return True
    return False


def scan_hr_folder(folder_path: str) -> list[dict]:
    folder = Path(folder_path)
    if not folder.exists():
        raise ValueError(f"Folder does not exist: {folder_path}")
    if not folder.is_dir():
        raise ValueError(f"Path is not a folder: {folder_path}")

    xlsx_files = sorted(folder.glob("*.xlsx"))
    if not xlsx_files:
        raise ValueError("No .xlsx files found in the folder.")

    invalid = []
    valid = []
    seen_display_labels: set[str] = set()

    for f in xlsx_files:
        m = HR_FILE_RE.match(f.name)
        if not m:
            if _hr_folder_skip_non_snapshot_xlsx(f.name):
                continue
            invalid.append(f.name)
            continue

        year = int(m.group(1))
        month = int(m.group(2))
        day = int(m.group(3))
        month_key = (year, month, day)
        file_stem = f.stem

        display_label = format_snapshot_date(year, month, day)
        if display_label in seen_display_labels:
            display_label = f"{display_label} – {file_stem}"
        seen_display_labels.add(display_label)

        valid.append(
            {
                "path": f,
                "year": year,
                "month": month,
                "day": day,
                "file_name": f.name,
                "month_key": month_key,
                "month_short": display_label,
                "month_label": display_label,
                "mtime": f.stat().st_mtime,
            }
        )

    if invalid:
        raise ValueError(
            "Invalid HR file name(s) found. Allowed format is exactly HRMS_YYYY_MM_DD.xlsx. "
            f"Invalid files: {invalid}"
        )

    valid = sorted(valid, key=lambda x: x["month_key"])
    if len(valid) < 2:
        raise ValueError("At least 2 valid HR files are required.")

    return valid


def validate_hrms_filename(filename: str) -> tuple[int, int, int] | None:
    """Return (year, month, day) if valid HRMS filename, else None."""
    m = HR_FILE_RE.match(filename)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))
