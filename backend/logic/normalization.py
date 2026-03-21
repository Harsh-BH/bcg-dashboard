import pandas as pd

from logic.utils import keyify


def normalize_hr_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}

    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee no", "employee number", "employee_id"],
        "BUSINESS UNIT": ["business unit", "businessunit", "bu"],
        "BUSINESS": ["business"],
        "EMPLOYEE TYPE": ["employee type", "employeetype", "emp type", "employee_type", "emp_type"],
        "LEVEL": ["level", "employee level"],
        "DESIGNATION": ["designation", "designation name", "role", "title"],
        "GRADE": ["grade", "employee grade", "emp grade"],
        "SEPARATION": ["separation", "separations", "separation status", "separation_status", "separationstatus"],
    }

    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    return df.rename(columns=rename)


def normalize_spartan_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}

    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee number", "employee_id"],
        "SPARTAN CATEGORY": ["spartan category", "category", "status", "spartan status", "spartan_category"],
        "LWD": ["lwd", "last working date", "lastworkingdate", "last working day", "lastworkingday"],
        "NAME": ["name", "employee name", "full name", "emp name"],
        "D3": ["d3"],
    }

    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    return df.rename(columns=rename)


def normalize_payroll_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}

    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee number", "employee_id", "emp code"],
        "EMPLOYEE NAME": ["employee name", "name", "emp name"],
    }

    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    return df.rename(columns=rename)


def normalize_span_hrms_cols(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names for Span HRMS file."""
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}
    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee number", "employee_id", "employee-id"],
        "MANAGER1 ECODE": [
            "manager1 ecode", "manager ecode", "manager1 e code", "manager_ecode",
            "reporting manager id", "manager id", "managerid", "manager_id",
            "reporting manager", "manager emp id", "manager employee id", "manager empid",
        ],
        "GRADE": ["grade", "employee grade", "emp grade"],
        "LEVEL": ["level", "employee level"],
        "DESIGNATION": ["designation", "designation name", "role", "title"],
        "BUSINESS UNIT": ["business unit", "businessunit", "bu"],
        "BUSINESS": ["business"],
        "PROCESS": ["process", "process name", "process description"],
        "DIVISION": ["division", "emp division", "employee division", "division name", "div"],
        "JOB_FUNCTION": ["job function", "jobfunction", "job_function", "function", "job role", "jobfunction name", "employee job function"],
        "ACCOUNT NAME": ["account name", "account_name", "client name", "account"],
        "LEGAL EMPLOYER NAME": ["legal employer name", "legal_employer_name", "legal employer"],
        "MANPOWER": ["manpower"],
        "SEPARATIONS": ["separations", "separation", "separation_status", "separation status"],
        "SUB PROCESS": ["sub process", "sub_process", "subprocess"],
        "MANPOWER CHECK": ["manpower check", "manpower_check", "manpowercheck", "mp check", "man power check"],
        "COST CENTER": ["cost center", "costcenter", "cost_center", "cost centre", "cc", "cost centre code"],
    }
    rename = {}
    for std, alist in aliases.items():
        for a in alist:
            if a in col_map:
                rename[col_map[a]] = std
                break
    out = df.rename(columns=rename)
    # Fallback: column literally named FUNCTION → JOB_FUNCTION
    if "JOB_FUNCTION" not in out.columns:
        fn_col = None
        for c in out.columns:
            if keyify(str(c)) == "function":
                fn_col = c
                break
        if fn_col is not None:
            out = out.rename(columns={fn_col: "JOB_FUNCTION"})
    return out
