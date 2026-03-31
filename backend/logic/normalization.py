import pandas as pd

from logic.utils import keyify


def normalize_hr_cols(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = df.columns.astype(str).str.strip()
    col_map = {keyify(c): c for c in df.columns}

    aliases = {
        "EMPLOYEE ID": ["employee id", "employeeid", "emp id", "empid", "employee code", "employee no", "employee number", "employee_id"],
        "ASSIGNMENT NUMBER": ["assignment number", "assignmentnumber", "assignment no", "assignment_number", "assign number", "assign no"],
        "NAME": ["name", "employee name", "full name", "emp name", "employeename", "employee_name"],
        "DATE OF JOINING": ["date of joining", "dateofjoining", "doj", "joining date", "date_of_joining", "joining_date", "join date"],
        "EMPLOYEE TYPE": ["employee type", "employeetype", "emp type", "employee_type", "emp_type"],
        "LEVEL": ["level", "employee level"],
        "DESIGNATION": ["designation", "designation name", "role", "title"],
        "BILLABLE NON BILLABLE": [
            "billable non billable", "billable non-billable", "billable/non billable",
            "billable_non_billable", "billed non billed", "billable", "billability",
        ],
        "WORK LOCATION": ["work location", "worklocation", "work_location", "office location", "location"],
        "STATE": ["state", "emp state"],
        "REGION": ["region", "emp region"],
        "COUNTRY": ["country", "emp country"],
        "EMPLOYEE STATUS": ["employee status", "employeestatus", "emp status", "employment status", "employee_status"],
        "EMPLOYMENT TYPE": ["employment type", "employmenttype", "employment_type", "contract type", "contracttype"],
        "BUSINESS UNIT": ["business unit", "businessunit", "bu"],
        "BUSINESS": ["business"],
        "DIVISION": ["division", "emp division", "employee division", "division name", "div"],
        "PROCESS": ["process", "process name", "process description"],
        "SUB PROCESS": ["sub process", "sub_process", "subprocess", "sub process name"],
        "ORGANIZATION TYPE": ["organization type", "org type", "organisation type", "org_type", "organization_type", "organisationtype"],
        "JOB FUNCTION": ["job function", "jobfunction", "job_function", "function", "job role", "jobfunction name", "employee job function"],
        "SUB FUNCTION": ["sub function", "subfunction", "sub_function", "sub function name", "sub_function name"],
        "JOB FAMILY": ["job family", "jobfamily", "job_family", "job family name"],
        "SUB FAMILY": ["sub family", "subfamily", "sub_family", "sub family name"],
        "COST CENTER": ["cost center", "costcenter", "cost_center", "cost centre", "cc", "cost centre code"],
        "COST CENTER NAME": ["cost center name", "costcentername", "cost_center_name", "cost centre name", "cost center desc"],
        "MANAGER1 ECODE": [
            "manager1 ecode", "manager ecode", "manager1 e code", "manager_ecode",
            "reporting manager id", "reporting manager", "manager id", "managerid", "manager_id",
            "manager emp id", "manager employee id", "manager empid",
        ],
        "MANAGER1 EMPNAME": [
            "manager1 empname", "manager empname", "manager1 emp name", "manager_empname",
            "reporting manager name", "manager name", "manager emp name", "manager employee name",
        ],
        "GRADE": ["grade", "employee grade", "emp grade"],
        "SEPARATION": ["separation", "separations", "separation status", "separation_status", "separationstatus"],
        "OTC PA": ["otc pa", "otc_pa", "otcpa", "otc p.a", "otc p a", "otc/pa"],
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
        "ACCOUNT NAME": ["account name", "account_name", "customer name", "customer_name", "customername", "customer", "client name", "account"],
        "LEGAL EMPLOYER NAME": ["legal employer name", "legal_employer_name", "legal employer"],
        "MANPOWER": ["manpower"],
        "SEPARATIONS": ["separations", "separation", "separation_status", "separation status"],
        "SUB PROCESS": ["sub process", "sub_process", "subprocess"],
        "MANPOWER CHECK": ["manpower check", "manpower_check", "manpowercheck", "mp check", "man power check"],
        "COST CENTER": ["cost center", "costcenter", "cost_center", "cost centre", "cc", "cost centre code"],
        # Pivot/analysis workbook columns (app.py Conneqt analysis files)
        "MAPPING":              ["mapping"],
        "AGG SERVICE LINE":     ["agg service line", "agg_service_line", "agg service-line"],
        "UPDATED BUSINESS UNIT":["updated business unit", "updated_business_unit"],
        "EXCLUSION":            ["exclusion"],
        "IC FLAG":              ["ic flag", "ic_flag", "icflag", "ic flag2"],
        "TL FLAG":              ["tl flag", "tl_flag", "tlflag"],
        "M1 FLAG":              ["m1 flag", "m1_flag", "m1flag"],
        "M2 FLAG":              ["m2 flag", "m2_flag", "m2flag"],
        "M3 FLAG":              ["m3 flag", "m3_flag", "m3flag"],
        "M4+ FLAG":             ["m4+ flag", "m4+_flag", "m4 flag", "m4plus flag"],
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
