"""
Generate mock HRMS / Spartan / Payroll / Conneqt-mapping XLSX files for dashboard testing.
Run from any directory:  python mock_data/generate_mock.py
"""

import random
import string
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)
OUT = Path(__file__).parent


# ─── helpers ──────────────────────────────────────────────────────────────────

def rand_id(prefix="E"):
    return prefix + "".join(random.choices(string.digits, k=6))


FIRST_NAMES = [
    "Arun","Priya","Rahul","Sneha","Vikram","Anjali","Deepak","Kavya",
    "Suresh","Meena","Arjun","Divya","Ravi","Pooja","Karan","Nisha",
    "Amit","Sunita","Sanjay","Rekha","Manish","Geeta","Naveen","Shilpa",
    "Rohit","Anita","Vikas","Preeti","Ajay","Usha","Nikhil","Swati",
    "Abhinav","Shruti","Gaurav","Ritika","Vishal","Monika","Sumit","Pallavi",
    "Harish","Vandana","Sachin","Manju","Tarun","Hemant","Rakesh","Chitra",
]
LAST_NAMES = [
    "Kumar","Sharma","Singh","Verma","Gupta","Yadav","Patel","Reddy",
    "Mishra","Joshi","Mehta","Nair","Iyer","Pillai","Das","Roy",
    "Chopra","Malhotra","Kapoor","Tiwari","Dubey","Pandey","Saxena","Srivastava",
]

def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def rand_doj():
    """Random date-of-joining within last 6 years."""
    start = date(2019, 1, 1)
    end   = date(2025, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def rand_assign(eid: str) -> str:
    return "E" + eid.lstrip("E")  # mirrors employee id with E prefix


DESIGNATIONS_IC = [
    "Collection Executive","Customer Relationship Executive","Tele Caller",
    "Operations Executive","Customer Care Executive","Field Officer",
    "Process Executive","Data Entry Operator","Back Office Executive",
    "FOS Executive","Accounts Executive","Finance Executive",
]
DESIGNATIONS_TL = [
    "Team Lead","Team Leader","Senior Team Lead","Team Manager","Supervisor",
    "Senior Officer","Lead - Operations",
]
DESIGNATIONS_M1 = [
    "Manager","Assistant Manager","Deputy Manager","Senior Manager",
    "Manager - Operations","Operations Manager",
]
DESIGNATIONS_SR = [
    "Senior Manager","General Manager","Vice President","Senior Vice President",
    "Director Operations","AVP","DGM","AGM",
]

GRADES_IC = ["A1.1","A1.2","A1.3","PT","AT","NAPS","NATS"]
GRADES_TL = ["A2.1","A2.2","A3","A4"]
GRADES_M1 = ["A5","E1","E2","E3"]
GRADES_SR = ["E4","E5","E6","E7","E8"]

PROCESSES = [
    "Collections","CLM","F&A Back Office","Quality Assurance",
    "Training","WFM","HR Operations","IT Support",
]
SUB_PROCESSES = {
    "Collections": ["Early Bucket","Mid Bucket","Hard Bucket"],
    "CLM":         ["CLM Domestic","CLM International"],
    "F&A Back Office": ["Accounts Payable","Accounts Receivable","Payroll"],
    "Quality Assurance": ["Call Audit","Process Audit"],
    "Training":    ["Induction","Upskilling","Leadership Dev"],
    "WFM":         ["Scheduling","Reporting","Forecasting"],
    "HR Operations": ["Recruitment","HRBP","Payroll"],
    "IT Support":  ["L1 Support","L2 Support","Infrastructure"],
}
DIVISIONS = [
    "CLM Domestic BFSI","Customer Service","Collections Operations",
    "Back Office Finance","WFM Analytics","Training & Development",
]
JOB_FUNCTIONS = ["Operations","Finance","Technology","Human Resources","Quality","Training","Analytics"]
SUB_FUNCTIONS = {
    "Operations":       ["Delivery","Process Management","Client Servicing"],
    "Finance":          ["Accounts","Budgeting","Compliance"],
    "Technology":       ["Development","Infrastructure","Data"],
    "Human Resources":  ["Talent Acquisition","HRBP","Learning & Development"],
    "Quality":          ["Audit","Reporting","Calibration"],
    "Training":         ["Facilitation","Content","Assessment"],
    "Analytics":        ["Reporting","Forecasting","BI"],
}
JOB_FAMILIES = ["Operations Management","Finance & Accounts","Technology","HR","QA","Training","Analytics"]
SUB_FAMILIES  = ["Core Operations","Support","Leadership","Specialist","Generalist"]
ORG_TYPES     = ["Sales","Operations","Support","Technology","Corporate"]

LOCATIONS = [
    ("Pune",        "Maharashtra", "West"),
    ("Mumbai",      "Maharashtra", "West"),
    ("Delhi",       "Delhi",       "North"),
    ("Noida",       "Uttar Pradesh","North"),
    ("Bengaluru",   "Karnataka",   "South"),
    ("Hyderabad",   "Telangana",   "South"),
    ("Chennai",     "Tamil Nadu",  "South"),
    ("Kolkata",     "West Bengal", "East"),
    ("Ahmedabad",   "Gujarat",     "West"),
    ("Jaipur",      "Rajasthan",   "North"),
]

COST_CENTERS = [
    ("40FSHBLAG1",  "FSHB Laguna Branch 1",     "Collections"),
    ("40FSHBLAGR",  "FSHB Laguna Grand",          "Collections"),
    ("40FSHBLTW1",  "FSHB Laguna Twin",           "Collections"),
    ("40LDHBLAGR",  "LDH Laguna Grand",           "Collections"),
    ("40KOSBITCO",  "KOS BIT Collections",        "CLM"),
    ("40RBSBITCO",  "RBS BIT Collections",        "CLM"),
    ("40KOSBITC1",  "KOS BIT Collections 1",      "Collections"),
    ("40ARTAIGCC",  "ART AIG Collections CLM",    "CLM"),
    ("40ARGHFL2E",  "ARG HFL Back Office",        "F&A Back Office"),
    ("40KSGHFINV",  "KSG HF Invoicing",           "F&A Back Office"),
    ("40KONABPLM",  "KONA BPL Collections",       "Collections"),
    ("CC001",       "Corporate HQ",               "Support"),
    ("CC002",       "Technology Centre",          "Technology"),
    ("CC003",       "Support Services",           "Support"),
    ("CC004",       "Training Hub",               "Training"),
    ("CC005",       "WFM Centre",                 "WFM"),
]

# Cost Center lookup dicts
CC_NAME = {cc: name for cc, name, _ in COST_CENTERS}
CC_CLUSTER = {cc: cluster for cc, _, cluster in COST_CENTERS}

ACCOUNTS = [
    "HDFC Bank","Bajaj Finance","Axis Bank","ICICI Bank","SBI Cards",
    "Kotak Mahindra","Yes Bank","IndusInd","Shriram Finance","Tata Capital",
]


# ─── single-row builders ──────────────────────────────────────────────────────

def _base_row(eid: str, name: str, bu: str, business: str, level: str,
              desig: str, grade: str, mgr_id: str, mgr_name: str,
              process: str, division: str, job_fn: str, cost_center: str,
              emp_type: str = "E", billable: str = "Billable",
              account: str = "Corporate") -> dict:
    loc, state, region = random.choice(LOCATIONS)
    sub_proc  = random.choice(SUB_PROCESSES.get(process, [process]))
    sub_fn    = random.choice(SUB_FUNCTIONS.get(job_fn, ["General"]))
    jf        = random.choice(JOB_FAMILIES)
    sf        = random.choice(SUB_FAMILIES)
    org_type  = random.choice(ORG_TYPES)
    cc_name   = CC_NAME.get(cost_center, cost_center)

    return {
        "EMPLOYEE ID":         eid,
        "ASSIGNMENT NUMBER":   rand_assign(eid),
        "NAME":                name,
        "DATE OF JOINING":     rand_doj().strftime("%d-%b-%Y"),
        "EMPLOYEE_TYPE":       emp_type,
        "LEVEL":               level,
        "DESIGNATION":         desig,
        "Billable Non Billable": billable,
        "WORK LOCATION":       loc,
        "State":               state,
        "REGION":              region,
        "COUNTRY":             "India",
        "EMPLOYEE STATUS":     "ACTIVE",
        "EMPLOYMENT TYPE":     "Permanent" if emp_type == "E" else "Contract",
        "Business Unit":       bu,
        "Business":            business,
        "DIVISION":            division,
        "PROCESS":             process,
        "SUB PROCESS":         sub_proc,
        "Organization Type":   org_type,
        "JOB_FUNCTION":        job_fn,
        "SUB_FUNCTION":        sub_fn,
        "JOB FAMILY":          jf,
        "SUB FAMILY":          sf,
        "COST CENTER":         cost_center,
        "COST CENTER NAME":    cc_name,
        "MANAGER1 ECODE":      mgr_id,
        "MANAGER1 EMPNAME":    mgr_name,
        # Extra columns used by span / spartan logic
        "GRADE":               grade,
        "SEPARATION":          "",
        "ACCOUNT NAME":        account,
        "LEGAL EMPLOYER NAME": "Conneqt Business Solutions Ltd",
        "MANPOWER":            "Yes",
        "SEPARATIONS":         "",
        "MANPOWER CHECK":      "Yes",
    }


def _conneqt_row(eid, name, grades, desigs, mgr_id, mgr_name) -> dict:
    grade   = random.choice(grades)
    desig   = random.choice(desigs)
    process = random.choice(PROCESSES)
    division= random.choice(DIVISIONS)
    job_fn  = random.choice(JOB_FUNCTIONS)
    cc_code, cc_name, _ = random.choice(COST_CENTERS[:11])  # Conneqt cost centres
    return _base_row(
        eid, name,
        bu="Conneqt Business Solution",
        business="BPM - Practices & Ops",
        level=grade, desig=desig, grade=grade,
        mgr_id=mgr_id, mgr_name=mgr_name,
        process=process, division=division, job_fn=job_fn,
        cost_center=cc_code,
        account=random.choice(ACCOUNTS),
    )


# ─── HRMS snapshot ────────────────────────────────────────────────────────────

def make_hrms_snapshot(n_total=250, prev_ids=None, prev_rows=None,
                       exits_n=10, hires_n=15):
    """Build one HRMS snapshot DataFrame.

    prev_ids  – set of employee IDs from the previous snapshot
    prev_rows – dict id → row (carries forward unchanged employees)
    Returns (df, id_set, row_dict)
    """
    rows: list[dict] = []
    name_cache: dict[str, str] = {}   # eid → name, for mgr name lookups

    # ── CXO (5) ──────────────────────────────────────────────────────────────
    cxo_ids: list[str] = []
    for _ in range(5):
        eid  = rand_id()
        name = rand_name()
        cxo_ids.append(eid)
        name_cache[eid] = name
        rows.append(_base_row(
            eid, name,
            bu="CXO", business="BPM - Practices & Ops",
            level="CX1", desig=random.choice(["Vice President","Senior Vice President","Director"]),
            grade="E6", mgr_id="", mgr_name="",
            process="Management", division="CXO", job_fn="Leadership",
            cost_center="CC001", billable="Non-Billable",
        ))

    # ── Tech & Digital (15) ──────────────────────────────────────────────────
    tech_mgr_id   = rand_id()
    tech_mgr_name = rand_name()
    name_cache[tech_mgr_id] = tech_mgr_name
    rows.append(_base_row(
        tech_mgr_id, tech_mgr_name,
        bu="Tech & Digital", business="Tech & Digital",
        level="E2", desig="Senior Manager", grade="E2",
        mgr_id=cxo_ids[0], mgr_name=name_cache[cxo_ids[0]],
        process="Technology", division="IT", job_fn="Technology",
        cost_center="CC002", billable="Non-Billable",
    ))
    for _ in range(14):
        eid  = rand_id()
        name = rand_name()
        name_cache[eid] = name
        rows.append(_base_row(
            eid, name,
            bu="Tech & Digital", business="Tech & Digital",
            level="A3", desig=random.choice(["Software Developer","Analyst","QA Engineer","Data Analyst"]),
            grade=random.choice(["A3","A4","A5"]),
            mgr_id=tech_mgr_id, mgr_name=tech_mgr_name,
            process="Technology", division="IT", job_fn="Technology",
            cost_center="CC002", billable="Non-Billable",
        ))

    # ── Support Functions (5 × 4 = 20) ───────────────────────────────────────
    support_cats = [
        ("Support Function - HR",             "HR",      "Human Resources",      "CC003"),
        ("Support Function - Finance",        "Finance", "Finance & Accounts",   "CC003"),
        ("Support Function - Administration", "Admin",   "Administration",       "CC003"),
        ("Support Function - IT",             "IT",      "Information Technology","CC003"),
    ]
    for sf_bu, sf_biz, sf_func, sf_cc in support_cats:
        mgr_id   = rand_id()
        mgr_name = rand_name()
        name_cache[mgr_id] = mgr_name
        rows.append(_base_row(
            mgr_id, mgr_name,
            bu=sf_bu, business=sf_biz,
            level="A5", desig="Manager", grade="A5",
            mgr_id=cxo_ids[1], mgr_name=name_cache[cxo_ids[1]],
            process=sf_func, division=sf_func, job_fn=sf_func if sf_func in JOB_FUNCTIONS else "Operations",
            cost_center=sf_cc, billable="Non-Billable",
        ))
        for _ in range(4):
            eid  = rand_id()
            name = rand_name()
            name_cache[eid] = name
            rows.append(_base_row(
                eid, name,
                bu=sf_bu, business=sf_biz,
                level="A1.2", desig=random.choice(["Executive","Senior Executive","Associate"]),
                grade="A1.2",
                mgr_id=mgr_id, mgr_name=mgr_name,
                process=sf_func, division=sf_func, job_fn="Operations",
                cost_center=sf_cc, billable="Non-Billable",
            ))

    # ── Conneqt core delivery (fill to n_total) ───────────────────────────────
    conneqt_target = n_total - len(rows)

    # Carry-forward employees from previous snapshot
    carried: dict[str, dict] = {}
    if prev_ids and prev_rows:
        staying = list(prev_ids)
        random.shuffle(staying)
        exit_ids = set(staying[:exits_n])
        for eid in staying[exits_n:]:
            if eid in prev_rows:
                carried[eid] = dict(prev_rows[eid])

    new_n = max(0, conneqt_target - len(carried))

    # Build managers first so we can fill MANAGER1 EMPNAME
    m1_ids_names: list[tuple[str,str]] = []
    tl_ids_names: list[tuple[str,str]] = []

    for _ in range(max(1, new_n // 50)):
        eid  = rand_id()
        name = rand_name()
        name_cache[eid] = name
        m1_ids_names.append((eid, name))
        mgr_id, mgr_name = cxo_ids[2], name_cache[cxo_ids[2]]
        rows.append(_conneqt_row(eid, name,
                                  GRADES_M1, DESIGNATIONS_M1,
                                  mgr_id, mgr_name))

    for _ in range(max(1, new_n // 12)):
        eid  = rand_id()
        name = rand_name()
        name_cache[eid] = name
        tl_ids_names.append((eid, name))
        if m1_ids_names:
            mgr_id, mgr_name = random.choice(m1_ids_names)
        else:
            mgr_id, mgr_name = cxo_ids[2], name_cache[cxo_ids[2]]
        rows.append(_conneqt_row(eid, name,
                                  GRADES_TL, DESIGNATIONS_TL,
                                  mgr_id, mgr_name))

    ic_n = new_n - len(m1_ids_names) - len(tl_ids_names)
    for _ in range(max(0, ic_n)):
        eid  = rand_id()
        name = rand_name()
        name_cache[eid] = name
        if tl_ids_names:
            mgr_id, mgr_name = random.choice(tl_ids_names)
        else:
            mgr_id, mgr_name = cxo_ids[0], name_cache[cxo_ids[0]]
        rows.append(_conneqt_row(eid, name,
                                  GRADES_IC, DESIGNATIONS_IC,
                                  mgr_id, mgr_name))

    rows.extend(carried.values())

    # New hires
    for _ in range(hires_n):
        eid  = rand_id()
        name = rand_name()
        name_cache[eid] = name
        if tl_ids_names:
            mgr_id, mgr_name = random.choice(tl_ids_names)
        elif m1_ids_names:
            mgr_id, mgr_name = random.choice(m1_ids_names)
        else:
            mgr_id, mgr_name = cxo_ids[0], name_cache[cxo_ids[0]]
        rows.append(_conneqt_row(eid, name,
                                  GRADES_IC, DESIGNATIONS_IC,
                                  mgr_id, mgr_name))

    df = pd.DataFrame(rows).drop_duplicates(subset=["EMPLOYEE ID"])

    # Update MANAGER1 EMPNAME for carried rows that may reference stale names
    # (best-effort: fill blanks from name_cache)
    def fill_mgr_name(row):
        if not row.get("MANAGER1 EMPNAME") and row.get("MANAGER1 ECODE"):
            return name_cache.get(row["MANAGER1 ECODE"], "")
        return row.get("MANAGER1 EMPNAME", "")

    df["MANAGER1 EMPNAME"] = df.apply(fill_mgr_name, axis=1)

    id_set   = set(df["EMPLOYEE ID"])
    row_dict = {r["EMPLOYEE ID"]: r for r in df.to_dict("records")}
    return df, id_set, row_dict, name_cache


# ─── Spartan generator ────────────────────────────────────────────────────────

def make_spartan(exited_ids: list[str], names: dict[str, str], ref_date: date) -> pd.DataFrame:
    rows = []
    for eid in exited_ids:
        lwd = ref_date - timedelta(days=random.randint(5, 60))
        rows.append({
            "EMPLOYEE ID":       eid,
            "NAME":              names.get(eid, rand_name()),
            "SPARTAN CATEGORY":  random.choice(["Resigned","Terminated","Absconded","Retired"]),
            "LWD":               lwd.strftime("%Y-%m-%d"),
            "D3":                random.choice(["1","1","1",""]),  # ~75% active exits
        })
    return pd.DataFrame(rows)


# ─── Payroll generator ────────────────────────────────────────────────────────

def make_payroll(active_ids: set[str], names: dict[str, str]) -> pd.DataFrame:
    """HRMS active set with 5 missing + 3 phantom extras."""
    ids = list(active_ids)
    random.shuffle(ids)
    in_payroll    = ids[5:]
    extra_payroll = [rand_id() for _ in range(3)]
    rows = []
    for eid in in_payroll + extra_payroll:
        rows.append({
            "EMPLOYEE ID":   eid,
            "EMPLOYEE NAME": names.get(eid, rand_name()),
            "DESIGNATION":   "Employee",
            "DEPARTMENT":    "Operations",
        })
    return pd.DataFrame(rows)


# ─── Conneqt mapping generator ───────────────────────────────────────────────

def make_conneqt_mapping() -> pd.DataFrame:
    """Cost-code → Cluster mapping file for span analysis."""
    rows = [
        {"Cost Code": cc, "Cluster": cluster}
        for cc, _, cluster in COST_CENTERS
    ]
    return pd.DataFrame(rows)


# ─── main ─────────────────────────────────────────────────────────────────────

def save(df: pd.DataFrame, path: Path):
    df.to_excel(path, index=False)
    print(f"  ✓  {path.name}  ({len(df)} rows, {len(df.columns)} cols)")


def main():
    print("Generating mock data…\n")

    # Snapshot 1 — Dec 2025
    df1, ids1, rows1, names1 = make_hrms_snapshot(n_total=230, hires_n=0)
    save(df1, OUT / "HRMS_2025_12_31.xlsx")

    # Snapshot 2 — Jan 2026
    df2, ids2, rows2, names2 = make_hrms_snapshot(
        n_total=235, prev_ids=ids1, prev_rows=rows1, exits_n=12, hires_n=18)
    save(df2, OUT / "HRMS_2026_01_31.xlsx")

    # Snapshot 3 — Feb 2026
    df3, ids3, rows3, names3 = make_hrms_snapshot(
        n_total=240, prev_ids=ids2, prev_rows=rows2, exits_n=8, hires_n=14)
    save(df3, OUT / "HRMS_2026_02_28.xlsx")

    # Merged name dict for Spartan / Payroll
    all_names = {**names1, **names2, **names3}

    # Spartan — people who left between Jan and Feb
    exited_jan_to_feb = list(ids2 - ids3)[:20]
    spartan_df = make_spartan(exited_jan_to_feb, all_names, date(2026, 2, 28))
    save(spartan_df, OUT / "Spartan_D2_Feb2026.xlsx")

    # Payroll — Feb snapshot + 3 Spartan IDs still drawing salary
    spartan_ids_in_payroll = set(exited_jan_to_feb[:3])
    payroll_df = make_payroll(ids3 | spartan_ids_in_payroll, all_names)
    save(payroll_df, OUT / "Payroll_Feb2026.xlsx")

    # Conneqt cost-code cluster mapping
    mapping_df = make_conneqt_mapping()
    save(mapping_df, OUT / "Conneqt_CostCode_Mapping.xlsx")

    print(f"\nAll files written to: {OUT.resolve()}")
    print("\nUpload in dashboard:")
    print("  HRMS files:    HRMS_2025_12_31.xlsx, HRMS_2026_01_31.xlsx, HRMS_2026_02_28.xlsx")
    print("  Spartan file:  Spartan_D2_Feb2026.xlsx")
    print("  Payroll file:  Payroll_Feb2026.xlsx")
    print("  Mapping file:  Conneqt_CostCode_Mapping.xlsx")
    print("  Payroll cycle: 2026-02-01  →  2026-02-28")
    print()
    print("Mandatory columns present in each HRMS file:")
    mandatory = [
        "EMPLOYEE ID","ASSIGNMENT NUMBER","NAME","DATE OF JOINING",
        "EMPLOYEE_TYPE","LEVEL","DESIGNATION","Billable Non Billable",
        "WORK LOCATION","State","REGION","COUNTRY","EMPLOYEE STATUS",
        "EMPLOYMENT TYPE","Business Unit","Business","DIVISION","PROCESS",
        "SUB PROCESS","Organization Type","JOB_FUNCTION","SUB_FUNCTION",
        "JOB FAMILY","SUB FAMILY","COST CENTER","COST CENTER NAME",
        "MANAGER1 ECODE","MANAGER1 EMPNAME",
    ]
    for col in mandatory:
        present = col in df3.columns
        print(f"  {'✓' if present else '✗'}  {col}")


if __name__ == "__main__":
    main()
