"""
Generate mock HRMS / Spartan / Payroll XLSX files for dashboard testing.
Run from any directory:  python mock_data/generate_mock.py
"""

import os
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

GRADES_IC   = ["A1.1","A1.2","A1.3","PT","AT","NAPS","NATS"]
GRADES_TL   = ["A2.1","A2.2","A3","A4"]
GRADES_M1   = ["A5","E1","E2","E3"]
GRADES_SR   = ["E4","E5","E6","E7","E8"]

PROCESSES = [
    "Collections","CLM","F&A Back Office","Quality Assurance",
    "Training","WFM","HR Operations","IT Support",
]
DIVISIONS = [
    "CLM Domestic BFSI","Customer Service","Collections Operations",
    "Back Office Finance","WFM Analytics","Training & Development",
]
COST_CENTERS = [
    "40FSHBLAG1","40FSHBLAGR","40FSHBLTW1","40LDHBLAGR","40KOSBITCO",
    "40RBSBITCO","40KOSBITC1","40ARTAIGCC","40ARGHFL2E","40KSGHFINV",
    "40KONABPLM","CC001","CC002","CC003","CC004","CC005",
]
ACCOUNTS = [
    "HDFC Bank","Bajaj Finance","Axis Bank","ICICI Bank","SBI Cards",
    "Kotak Mahindra","Yes Bank","IndusInd","Shriram Finance","Tata Capital",
]

# ─── HRMS generator ───────────────────────────────────────────────────────────

def make_hrms_snapshot(n_total=250, prev_ids=None, prev_rows=None, exits_n=10, hires_n=15):
    """
    Build a snapshot DataFrame.
    prev_ids  – set of employee IDs from the previous snapshot (for reconciliation)
    prev_rows – dict of id→row (to carry forward unchanged employees)
    exits_n   – how many from prev_ids leave between snapshots
    hires_n   – how many brand-new employees join
    Returns (df, id_set, row_dict)
    """
    rows = []

    # ── CXO employees (5) ──
    cxo_ids = [rand_id() for _ in range(5)]
    for eid in cxo_ids:
        rows.append({
            "EMPLOYEE ID": eid,
            "NAME": rand_name(),
            "BUSINESS UNIT": "CXO",
            "BUSINESS": "BPM - Practices & Ops",
            "EMPLOYEE TYPE": "E",
            "LEVEL": "CX1",
            "DESIGNATION": random.choice(["Vice President","Senior Vice President","Director"]),
            "GRADE": "E6",
            "SEPARATION": "",
            "MANAGER1 ECODE": "",
            "PROCESS": "Management",
            "DIVISION": "CXO",
            "JOB_FUNCTION": "Leadership",
            "ACCOUNT NAME": "Corporate",
            "LEGAL EMPLOYER NAME": "Conneqt Business Solutions Ltd",
            "MANPOWER": "Yes",
            "SEPARATIONS": "",
            "SUB PROCESS": "",
            "MANPOWER CHECK": "Yes",
            "COST CENTER": "CC001",
        })

    # ── Tech & Digital (15) ──
    tech_mgr_id = rand_id()
    rows.append({
        "EMPLOYEE ID": tech_mgr_id,
        "NAME": rand_name(),
        "BUSINESS UNIT": "Tech & Digital",
        "BUSINESS": "Tech & Digital",
        "EMPLOYEE TYPE": "E",
        "LEVEL": "E2",
        "DESIGNATION": "Senior Manager",
        "GRADE": "E2",
        "SEPARATION": "",
        "MANAGER1 ECODE": cxo_ids[0],
        "PROCESS": "Technology",
        "DIVISION": "IT",
        "JOB_FUNCTION": "Technology",
        "ACCOUNT NAME": "Corporate",
        "LEGAL EMPLOYER NAME": "Conneqt Business Solutions Ltd",
        "MANPOWER": "Yes",
        "SEPARATIONS": "",
        "SUB PROCESS": "",
        "MANPOWER CHECK": "Yes",
        "COST CENTER": "CC002",
    })
    for _ in range(14):
        eid = rand_id()
        rows.append({
            "EMPLOYEE ID": eid,
            "NAME": rand_name(),
            "BUSINESS UNIT": "Tech & Digital",
            "BUSINESS": "Tech & Digital",
            "EMPLOYEE TYPE": "E",
            "LEVEL": "A3",
            "DESIGNATION": random.choice(["Software Developer","Analyst","QA Engineer","Data Analyst"]),
            "GRADE": random.choice(["A3","A4","A5"]),
            "SEPARATION": "",
            "MANAGER1 ECODE": tech_mgr_id,
            "PROCESS": "Technology",
            "DIVISION": "IT",
            "JOB_FUNCTION": "Technology",
            "ACCOUNT NAME": "Corporate",
            "LEGAL EMPLOYER NAME": "Conneqt Business Solutions Ltd",
            "MANPOWER": "Yes",
            "SEPARATIONS": "",
            "SUB PROCESS": "",
            "MANPOWER CHECK": "Yes",
            "COST CENTER": "CC002",
        })

    # ── Support Functions (20) ──
    support_cats = [
        ("Support Function - HR","HR","Human Resources"),
        ("Support Function - Finance","Finance","Finance & Accounts"),
        ("Support Function - Administration","Admin","Administration"),
        ("Support Function - IT","IT","Information Technology"),
    ]
    for sf_bu, sf_biz, sf_func in support_cats:
        sf_mgr = rand_id()
        rows.append({
            "EMPLOYEE ID": sf_mgr,
            "NAME": rand_name(),
            "BUSINESS UNIT": sf_bu,
            "BUSINESS": sf_biz,
            "EMPLOYEE TYPE": "E",
            "LEVEL": "A5",
            "DESIGNATION": "Manager",
            "GRADE": "A5",
            "SEPARATION": "",
            "MANAGER1 ECODE": cxo_ids[1],
            "PROCESS": sf_func,
            "DIVISION": sf_func,
            "JOB_FUNCTION": sf_func,
            "ACCOUNT NAME": "Corporate",
            "LEGAL EMPLOYER NAME": "Conneqt Business Solutions Ltd",
            "MANPOWER": "Yes",
            "SEPARATIONS": "",
            "SUB PROCESS": "",
            "MANPOWER CHECK": "Yes",
            "COST CENTER": "CC003",
        })
        for _ in range(4):
            rows.append({
                "EMPLOYEE ID": rand_id(),
                "NAME": rand_name(),
                "BUSINESS UNIT": sf_bu,
                "BUSINESS": sf_biz,
                "EMPLOYEE TYPE": "E",
                "LEVEL": "A1.2",
                "DESIGNATION": random.choice(["Executive","Senior Executive","Associate"]),
                "GRADE": "A1.2",
                "SEPARATION": "",
                "MANAGER1 ECODE": sf_mgr,
                "PROCESS": sf_func,
                "DIVISION": sf_func,
                "JOB_FUNCTION": sf_func,
                "ACCOUNT NAME": "Corporate",
                "LEGAL EMPLOYER NAME": "Conneqt Business Solutions Ltd",
                "MANPOWER": "Yes",
                "SEPARATIONS": "",
                "SUB PROCESS": "",
                "MANPOWER CHECK": "Yes",
                "COST CENTER": "CC003",
            })

    # ── Conneqt core delivery (rest) ──
    conneqt_target = n_total - len(rows)

    # Build carry-forward employees if we have prev
    carried = {}
    if prev_ids and prev_rows:
        staying_ids = list(prev_ids)
        random.shuffle(staying_ids)
        exit_ids = set(staying_ids[:exits_n])
        carry_ids = staying_ids[exits_n:]
        for eid in carry_ids:
            if eid in prev_rows:
                carried[eid] = dict(prev_rows[eid])
        # mark exited in prev data (they won't appear here)

    new_conneqt_n = max(0, conneqt_target - len(carried))

    # Generate new Conneqt employees
    # First create TL/M1 managers
    tl_ids = [rand_id() for _ in range(max(1, new_conneqt_n // 12))]
    m1_ids = [rand_id() for _ in range(max(1, new_conneqt_n // 50))]

    for eid in m1_ids:
        rows.append(_conneqt_row(eid, rand_name(), GRADES_M1, DESIGNATIONS_M1, cxo_ids[2], PROCESSES, DIVISIONS))

    for eid in tl_ids:
        rows.append(_conneqt_row(eid, rand_name(), GRADES_TL, DESIGNATIONS_TL, random.choice(m1_ids), PROCESSES, DIVISIONS))

    ic_n = new_conneqt_n - len(tl_ids) - len(m1_ids)
    for _ in range(max(0, ic_n)):
        eid = rand_id()
        rows.append(_conneqt_row(eid, rand_name(), GRADES_IC, DESIGNATIONS_IC, random.choice(tl_ids), PROCESSES, DIVISIONS))

    # Append carried employees
    rows.extend(carried.values())

    # Add new hires (fresh IDs)
    for _ in range(hires_n):
        eid = rand_id()
        rows.append(_conneqt_row(eid, rand_name(), GRADES_IC, DESIGNATIONS_IC, random.choice(tl_ids) if tl_ids else rand_id(), PROCESSES, DIVISIONS))

    df = pd.DataFrame(rows).drop_duplicates(subset=["EMPLOYEE ID"])
    id_set = set(df["EMPLOYEE ID"])
    row_dict = {r["EMPLOYEE ID"]: r for r in df.to_dict("records")}
    return df, id_set, row_dict


def _conneqt_row(eid, name, grades, desigs, mgr_id, processes, divisions):
    grade = random.choice(grades)
    desig = random.choice(desigs)
    process = random.choice(processes)
    division = random.choice(divisions)
    return {
        "EMPLOYEE ID": eid,
        "NAME": name,
        "BUSINESS UNIT": "Conneqt Business Solution",
        "BUSINESS": "BPM - Practices & Ops",
        "EMPLOYEE TYPE": "E",
        "LEVEL": grade,
        "DESIGNATION": desig,
        "GRADE": grade,
        "SEPARATION": "",
        "MANAGER1 ECODE": mgr_id,
        "PROCESS": process,
        "DIVISION": division,
        "JOB_FUNCTION": "Operations",
        "ACCOUNT NAME": random.choice(ACCOUNTS),
        "LEGAL EMPLOYER NAME": "Conneqt Business Solutions Ltd",
        "MANPOWER": "Yes",
        "SEPARATIONS": "",
        "SUB PROCESS": process,
        "MANPOWER CHECK": "Yes",
        "COST CENTER": random.choice(COST_CENTERS),
    }


# ─── Spartan generator ────────────────────────────────────────────────────────

def make_spartan(exited_ids: list[str], names: dict[str, str], ref_date: date):
    """A D2 Spartan file — one row per exit."""
    rows = []
    for eid in exited_ids:
        lwd = ref_date - timedelta(days=random.randint(5, 60))
        rows.append({
            "EMPLOYEE ID": eid,
            "NAME": names.get(eid, rand_name()),
            "SPARTAN CATEGORY": random.choice(["Resigned","Terminated","Absconded","Retired"]),
            "LWD": lwd.strftime("%Y-%m-%d"),
            "D3": random.choice(["1", "1", "1", ""]),  # ~75% D3=1 (active exits)
        })
    # Add a few overdue (LWD in the past but still in HRMS in the latest snapshot — we'll include some IDs from active set)
    return pd.DataFrame(rows)


# ─── Payroll generator ────────────────────────────────────────────────────────

def make_payroll(active_ids: set[str], names: dict[str, str]):
    """
    Payroll file — mostly same as HRMS active, with a few mismatches:
      - 5 in HRMS not in payroll (probably new joiners not yet on payroll)
      - 3 in payroll not in HRMS (probably late exits)
    """
    ids = list(active_ids)
    random.shuffle(ids)

    in_payroll = ids[5:]   # first 5 are NOT on payroll
    extra_payroll = [rand_id() for _ in range(3)]  # 3 phantom payroll entries

    rows = []
    for eid in in_payroll + extra_payroll:
        rows.append({
            "EMPLOYEE ID": eid,
            "EMPLOYEE NAME": names.get(eid, rand_name()),
            "DESIGNATION": "Employee",
            "DEPARTMENT": "Operations",
        })
    return pd.DataFrame(rows)


# ─── main ─────────────────────────────────────────────────────────────────────

def save(df: pd.DataFrame, path: Path):
    df.to_excel(path, index=False)
    print(f"  ✓  {path.name}  ({len(df)} rows)")


def main():
    print("Generating mock data…\n")

    # Snapshot 1 — Dec 2025
    df1, ids1, rows1 = make_hrms_snapshot(n_total=230, hires_n=0)
    save(df1, OUT / "HRMS_2025_12_31.xlsx")

    # Snapshot 2 — Jan 2026 (some exits, some hires vs Dec)
    df2, ids2, rows2 = make_hrms_snapshot(n_total=235, prev_ids=ids1, prev_rows=rows1, exits_n=12, hires_n=18)
    save(df2, OUT / "HRMS_2026_01_31.xlsx")

    # Snapshot 3 — Feb 2026 (some exits, some hires vs Jan)
    df3, ids3, rows3 = make_hrms_snapshot(n_total=240, prev_ids=ids2, prev_rows=rows2, exits_n=8, hires_n=14)
    save(df3, OUT / "HRMS_2026_02_28.xlsx")

    # Spartan — list of people who exited (IDs that were in Jan but not Feb)
    exited_jan_to_feb = list(ids2 - ids3)[:20]  # take up to 20
    all_names = {r["EMPLOYEE ID"]: r["NAME"] for r in list(rows1.values()) + list(rows2.values()) + list(rows3.values())}
    spartan_df = make_spartan(exited_jan_to_feb, all_names, date(2026, 2, 28))
    save(spartan_df, OUT / "Spartan_D2_Feb2026.xlsx")

    # Payroll — based on Feb 2026 snapshot + 3 Spartan exited IDs still in payroll
    spartan_ids_still_in_payroll = set(exited_jan_to_feb[:3])
    payroll_df = make_payroll(ids3 | spartan_ids_still_in_payroll, all_names)
    save(payroll_df, OUT / "Payroll_Feb2026.xlsx")

    print(f"\nAll files written to: {OUT.resolve()}")
    print("\nUpload order in dashboard:")
    print("  HRMS files:    HRMS_2025_12_31.xlsx, HRMS_2026_01_31.xlsx, HRMS_2026_02_28.xlsx")
    print("  Spartan file:  Spartan_D2_Feb2026.xlsx")
    print("  Payroll file:  Payroll_Feb2026.xlsx")
    print("  Payroll cycle: 2026-02-01  →  2026-02-28")


if __name__ == "__main__":
    main()
