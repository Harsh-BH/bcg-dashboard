"""
Generate 5 months of realistic HRMS data — 50,000 rows each.
Matches the standardized column format (Mar-2026 style) that the backend
normalization layer handles cleanly.

Run:  python mock_data/generate_large.py
Output: mock_data/large/HRMS_YYYY_MM_DD.xlsx  (x5)
"""

import random
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta

random.seed(42)
np.random.seed(42)

OUT = Path(__file__).parent / "large"
OUT.mkdir(exist_ok=True)

N = 50_000  # rows per snapshot

# ── Months ────────────────────────────────────────────────────────────────────
MONTHS = [
    date(2025, 9, 30),
    date(2025, 10, 31),
    date(2025, 11, 30),
    date(2025, 12, 31),
    date(2026,  1, 31),
]

# ── Pools ─────────────────────────────────────────────────────────────────────
FIRST = ["Arun","Priya","Rahul","Sneha","Vikram","Anjali","Deepak","Kavya",
         "Suresh","Meena","Arjun","Divya","Ravi","Pooja","Karan","Nisha",
         "Amit","Sunita","Sanjay","Rekha","Manish","Geeta","Naveen","Shilpa",
         "Rohit","Anita","Vikas","Preeti","Ajay","Usha","Nikhil","Swati",
         "Mohammed","Namita","Gaurav","Ritika","Vishal","Monika","Sumit","Pallavi",
         "Harish","Vandana","Sachin","Tarun","Hemant","Bristi","Jayanta","Malini"]
LAST  = ["Kumar","Sharma","Singh","Verma","Gupta","Yadav","Patel","Reddy",
         "Mishra","Joshi","Mehta","Nair","Iyer","Pillai","Das","Roy",
         "Chopra","Malhotra","Kapoor","Tiwari","Dubey","Pandey","Saxena",
         "Srivastava","Deb","Kalita","Chouhan","Hembram","Ali","Sarkar"]

LOCATIONS = ["Hyderabad Hub","Kolkata Hub","Mumbai Hub","Chennai Hub","Pune Hub",
             "Bangalore Hub","Jamshedpur Hub","Noida Hub","Ahmedabad Hub","Delhi Hub"]
STATES    = ["Telangana","West Bengal","Maharashtra","Tamil Nadu","Maharashtra",
             "Karnataka","Jharkhand","Uttar Pradesh","Gujarat","Delhi"]
REGIONS   = ["South","East","West","South","West","South","East","North","West","North"]

GRADES_IC = ["A1.1","A1.2","A1.3","PT","AT","NAPS","NATS"]
GRADES_TL = ["A2.1","A2.2","A3","A4","A5"]
GRADES_M1 = ["E1","E2"]
GRADES_M2 = ["E3","E4"]
GRADES_M3 = ["E5","E6"]
GRADES_CXO= ["CX1","CX2","CX3","CXO"]

DESIG_IC  = ["Customer Care Executive","CCE","Tele Caller","Apprentice-Customer Care",
             "FOS Executive","Collection Executive","Customer Relationship Executive","Sr. CCE"]
DESIG_TL  = ["Team Lead","Team Leader","Supervisor","Senior Officer","Lead - Operations"]
DESIG_M1  = ["Assistant Manager","Deputy Manager","Manager"]
DESIG_M2  = ["Senior Manager","General Manager"]
DESIG_M3  = ["AVP","Vice President"]
DESIG_CXO = ["Director","Senior Vice President","Chief Officer","EVP"]

# Buckets and their (BU, Business, Division, Process) combos
BUCKET_SPECS = {
    "Conneqt Business Solution": {
        "bu": "Conneqt Business Solution",
        "business": "BPM - Practices & Ops",
        "divisions": ["Collections","CLM","F&A Back Office","WFM","Quality","Training"],
        "processes": [
            "Collections | Telecollection","Collections | FOS",
            "CLM Domestic BFSI | Inbound","CLM Domestic BFSI | Outbound",
            "CLM Domestic BFSI | Back Office","CLM Domestic Diversified | Inbound",
            "CLM Domestic Diversified | Outbound","CLM International | Inbound",
            "F&A Back Office | Invoice Processing","F&A Back Office | Reconciliation",
        ],
        "accounts": ["HDFC Bank","ICICI Bank","Axis Bank","SBI","Kotak Mahindra","Yes Bank","Bajaj Finance","Swiggy","Zomato","Amazon"],
        "weight": 0.55,
    },
    "Alldigi": {
        "bu": "Alldigi",
        "business": "BPM - Practices & Ops",
        "divisions": ["Operations","Quality","Training","WFM"],
        "processes": ["Alldigi Collections","Alldigi CLM","Alldigi Quality","Alldigi WFM"],
        "accounts": ["Alldigi Internal","Alldigi Ops","Alldigi QA"],
        "weight": 0.10,
    },
    "Tech & Digital": {
        "bu": "Tech & Digital",
        "business": "Tech & Digital",
        "divisions": ["Digital Automation","Analytics","IT Infrastructure","Product"],
        "processes": ["Digital Automation | Dev","Analytics | BI","IT Infra | Cloud","Product | Mgmt"],
        "accounts": ["Internal Tech","Digital Hub","Analytics CoE"],
        "weight": 0.08,
    },
    "CXO": {
        "bu": "CXO",
        "business": "CXO",
        "divisions": ["Leadership","Strategy"],
        "processes": ["Group Leadership","Strategic Initiatives"],
        "accounts": ["Corporate"],
        "weight": 0.02,
    },
    "Support Functions - HR": {
        "bu": "Support Function - HR",
        "business": "HR",
        "divisions": ["HRBP","Talent Acquisition","L&D"],
        "processes": ["HRBP | Business","Talent Acquisition | Recruiting","L&D | Training"],
        "accounts": ["HR Shared Services"],
        "weight": 0.05,
    },
    "Support Functions - Finance": {
        "bu": "Support Function - Finance",
        "business": "Finance",
        "divisions": ["Payroll","Accounts","FP&A"],
        "processes": ["Payroll Processing","Accounts Payable","FP&A | Budgeting"],
        "accounts": ["Finance Shared Services"],
        "weight": 0.05,
    },
    "Support Functions - Admin": {
        "bu": "Support Function - Admin",
        "business": "Administration",
        "divisions": ["Facilities","Transport","IT Support"],
        "processes": ["Facilities Mgmt","Transport Ops","IT Helpdesk"],
        "accounts": ["Admin Shared Services"],
        "weight": 0.05,
    },
    "Support Functions - IT": {
        "bu": "Support Function - IT",
        "business": "IT",
        "divisions": ["Infrastructure","Security","Applications"],
        "processes": ["IT Infra | DC Ops","IT Security | SOC","App Support | L2"],
        "accounts": ["IT Shared Services"],
        "weight": 0.05,
    },
    "Support Functions - Legal": {
        "bu": "Support Function - Legal",
        "business": "Legal & Compliance",
        "divisions": ["Legal","Compliance"],
        "processes": ["Legal | Contracts","Compliance | Regulatory"],
        "accounts": ["Legal Shared Services"],
        "weight": 0.05,
    },
}

BUCKET_NAMES  = list(BUCKET_SPECS.keys())
BUCKET_WEIGHTS= [BUCKET_SPECS[b]["weight"] for b in BUCKET_NAMES]

# Grade mix per bucket  (IC%, TL%, M1%, M2%, M3%, CXO%)
GRADE_MIX = {
    "Conneqt Business Solution": [0.75, 0.15, 0.07, 0.02, 0.01, 0.00],
    "Alldigi":                   [0.72, 0.17, 0.08, 0.02, 0.01, 0.00],
    "Tech & Digital":            [0.50, 0.20, 0.18, 0.08, 0.03, 0.01],
    "CXO":                       [0.00, 0.00, 0.10, 0.20, 0.30, 0.40],
    "Support Functions - HR":    [0.40, 0.20, 0.25, 0.10, 0.04, 0.01],
    "Support Functions - Finance":[0.40,0.20, 0.25, 0.10, 0.04, 0.01],
    "Support Functions - Admin": [0.45, 0.25, 0.20, 0.08, 0.02, 0.00],
    "Support Functions - IT":    [0.45, 0.20, 0.22, 0.10, 0.02, 0.01],
    "Support Functions - Legal": [0.30, 0.15, 0.30, 0.15, 0.08, 0.02],
}

OTC_RANGE = {
    "IC":  (80_000,  200_000),
    "TL":  (150_000, 350_000),
    "M1":  (320_000, 620_000),
    "M2":  (600_000, 1_200_000),
    "M3":  (1_200_000, 2_500_000),
    "CXO": (2_500_000, 8_000_000),
}


def _grade_band(grade):
    g = grade.upper()
    if g in {g2.upper() for g2 in GRADES_IC}:  return "IC"
    if g in {g2.upper() for g2 in GRADES_TL}:  return "TL"
    if g in {g2.upper() for g2 in GRADES_M1}:  return "M1"
    if g in {g2.upper() for g2 in GRADES_M2}:  return "M2"
    if g in {g2.upper() for g2 in GRADES_M3}:  return "M3"
    return "CXO"


def build_employee_pool(n: int) -> pd.DataFrame:
    """Build a stable pool of N employees with fixed IDs and attributes."""
    rng = np.random.default_rng(0)

    emp_ids = rng.integers(100_000, 999_999, size=n)
    # ensure unique
    emp_ids = np.unique(emp_ids)
    while len(emp_ids) < n:
        extra = rng.integers(100_000, 999_999, size=n - len(emp_ids))
        emp_ids = np.unique(np.concatenate([emp_ids, extra]))
    emp_ids = emp_ids[:n]

    buckets = rng.choice(BUCKET_NAMES, size=n, p=BUCKET_WEIGHTS)

    grades, desigs, bands = [], [], []
    for b in buckets:
        mix = GRADE_MIX[b]
        band = rng.choice(["IC","TL","M1","M2","M3","CXO"], p=mix)
        bands.append(band)
        if band == "IC":
            grades.append(rng.choice(GRADES_IC)); desigs.append(rng.choice(DESIG_IC))
        elif band == "TL":
            grades.append(rng.choice(GRADES_TL)); desigs.append(rng.choice(DESIG_TL))
        elif band == "M1":
            grades.append(rng.choice(GRADES_M1)); desigs.append(rng.choice(DESIG_M1))
        elif band == "M2":
            grades.append(rng.choice(GRADES_M2)); desigs.append(rng.choice(DESIG_M2))
        elif band == "M3":
            grades.append(rng.choice(GRADES_M3)); desigs.append(rng.choice(DESIG_M3))
        else:
            grades.append(rng.choice(GRADES_CXO)); desigs.append(rng.choice(DESIG_CXO))

    loc_idx  = rng.integers(0, len(LOCATIONS), size=n)
    doj_days = rng.integers(0, (date(2025,8,1) - date(2018,1,1)).days, size=n)
    doj_base = date(2018,1,1)

    names   = [f"{random.choice(FIRST)} {random.choice(LAST)}" for _ in range(n)]
    otc_pa  = [
        int(rng.integers(*OTC_RANGE[b], endpoint=True))
        for b in bands
    ]
    assign_nums = [f"F{eid+10000}" for eid in emp_ids]

    # manager pool: pick a random non-IC employee as manager
    # (simplified: just pick random IDs from the pool itself)
    mgr_ids = rng.choice(emp_ids, size=n)

    return pd.DataFrame({
        "_emp_id":     emp_ids,
        "_name":       names,
        "_assign":     assign_nums,
        "_doj_days":   doj_days,
        "_bucket":     buckets,
        "_band":       bands,
        "_grade":      grades,
        "_desig":      desigs,
        "_loc_idx":    loc_idx,
        "_otc":        otc_pa,
        "_mgr_id":     mgr_ids,
    })


def snapshot_for_month(pool: pd.DataFrame, snap_date: date, churn_rate: float = 0.03) -> pd.DataFrame:
    """
    From the stable pool, sample ~N rows with small churn between months.
    churn_rate = fraction replaced with new joinees each month.
    """
    rng = np.random.default_rng(snap_date.toordinal())
    n = len(pool)

    # Drop ~churn_rate fraction, replace with others from pool
    keep_mask = rng.random(n) > churn_rate
    kept = pool[keep_mask].copy()
    # Fill back to N by sampling from dropped rows (simulates new hires)
    n_new = n - len(kept)
    new_rows = pool[~keep_mask].sample(n=min(n_new, len(pool[~keep_mask])),
                                        random_state=snap_date.toordinal(), replace=True)
    # Give new joiners a recent DOJ
    new_rows = new_rows.copy()
    new_rows["_doj_days"] = rng.integers(
        (snap_date - date(2018,1,1)).days - 90,
        (snap_date - date(2018,1,1)).days,
        size=len(new_rows)
    ).clip(0)
    df = pd.concat([kept, new_rows], ignore_index=True).head(n)

    doj_base = date(2018, 1, 1)

    rows = []
    for _, r in df.iterrows():
        b     = r["_bucket"]
        spec  = BUCKET_SPECS[b]
        li    = int(r["_loc_idx"]) % len(LOCATIONS)
        doj   = doj_base + timedelta(days=int(r["_doj_days"]))
        div   = random.choice(spec["divisions"])
        proc  = random.choice(spec["processes"])

        rows.append({
            "EMPLOYEE ID":      int(r["_emp_id"]),
            "ASSIGNMENT NUMBER":r["_assign"],
            "NAME":             r["_name"],
            "DATE OF JOINING":  doj.strftime("%d-%b-%Y"),
            "EMPLOYEE TYPE":    "E",
            "LEVEL":            r["_grade"],
            "DESIGNATION":      r["_desig"],
            "BILLABLE NON BILLABLE": "Billable" if r["_band"] == "IC" else "Non-Billable",
            "WORK LOCATION":    LOCATIONS[li],
            "STATE":            STATES[li],
            "REGION":           REGIONS[li],
            "COUNTRY":          "India",
            "EMPLOYEE STATUS":  "ACTIVE",
            "EMPLOYMENT TYPE":  "Permanent",
            "BUSINESS UNIT":    spec["bu"],
            "BUSINESS":         spec["business"],
            "DIVISION":         div,
            "PROCESS":          proc,
            "SUB PROCESS":      proc + " | Sub",
            "ORGANIZATION TYPE":"Delivery" if b in ("Conneqt Business Solution","Alldigi") else "Support",
            "JOB FUNCTION":     div,
            "SUB FUNCTION":     div + " Ops",
            "JOB FAMILY":       r["_band"] + " Role",
            "SUB FAMILY":       r["_desig"],
            "COST CENTER":      f"CC{int(r['_emp_id']) % 500:04d}",
            "COST CENTER NAME": spec["bu"] + " - " + div,
            "MANAGER1 ECODE":   int(r["_mgr_id"]),
            "MANAGER1 EMPNAME": "Manager Name",
            "SEPARATION":       0,
            "OTC PA":           int(r["_otc"]),
            "GRADE":            r["_grade"],
            "ACCOUNT NAME":     random.choice(spec["accounts"]),
        })

    return pd.DataFrame(rows)


def main():
    print(f"Building employee pool of {N:,} ...")
    pool = build_employee_pool(N)
    print(f"Pool built: {len(pool):,} unique employees")

    for snap_date in MONTHS:
        fname = OUT / f"HRMS_{snap_date.year}_{snap_date.month:02d}_{snap_date.day:02d}.xlsx"
        print(f"  Generating {fname.name} ...", end=" ", flush=True)
        df = snapshot_for_month(pool, snap_date)
        df.to_excel(fname, index=False, engine="openpyxl")
        print(f"{len(df):,} rows, {df.shape[1]} cols → {fname.stat().st_size/1024/1024:.1f} MB")

    print(f"\nDone. Files in: {OUT.resolve()}")


if __name__ == "__main__":
    main()
