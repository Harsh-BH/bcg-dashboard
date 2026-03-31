"""
Generate mock HRMS / Spartan / Payroll / Conneqt-mapping / Conneqt-analysis XLSX files.

File structure matches screenshots:
  Images 1+2 → HRMS_*.xlsx  (Employee ID, Grade, Name, Designation, OTC PA,
                               Work Location, Country, Business, Business unit,
                               Manager id, Check, Separation, Customer name,
                               Core delivery/delivery support, Cluster,
                               Classification, Manpower, PROCESS …)
  Images 3+4 → Conneqt_Jan_analysis_v4.xlsx  (Employee ID, Grade, Grade map,
                               Name, Designation, OTC PA, Work Location, Country,
                               Business, Business unit, Manager id, Check,
                               Present in, Separation, Sept Salary, Diff in Sal,
                               LWD, Spartan Category, Customer name,
                               IC flag, TL flag, M1 flag, M2 Flag, M3 Flag,
                               M4+ Flag, TL+, Service line, PROCESS,
                               COST CENTER, DIVISION, JOB_FUNCTION)

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

def rand_id(n=6):
    return "".join(random.choices(string.digits, k=n))


FIRST_NAMES = [
    "Arun", "Priya", "Rahul", "Sneha", "Vikram", "Anjali", "Deepak", "Kavya",
    "Suresh", "Meena", "Arjun", "Divya", "Ravi", "Pooja", "Karan", "Nisha",
    "Amit", "Sunita", "Sanjay", "Rekha", "Manish", "Geeta", "Naveen", "Shilpa",
    "Rohit", "Anita", "Vikas", "Preeti", "Ajay", "Usha", "Nikhil", "Swati",
    "Abhinav", "Shruti", "Gaurav", "Ritika", "Vishal", "Monika", "Sumit",
    "Pallavi", "Harish", "Vandana", "Sachin", "Manju", "Tarun", "Hemant",
    "Mohammed", "Namita", "Ganta", "Khushboo", "Sabiyah", "Aradhana",
    "Suresh", "Bristi", "Jayanta", "Nisha", "Shavez", "Malini", "Sukirtha",
]
LAST_NAMES = [
    "Kumar", "Sharma", "Singh", "Verma", "Gupta", "Yadav", "Patel", "Reddy",
    "Mishra", "Joshi", "Mehta", "Nair", "Iyer", "Pillai", "Das", "Roy",
    "Chopra", "Malhotra", "Kapoor", "Tiwari", "Dubey", "Pandey", "Saxena",
    "Srivastava", "Deb", "Kalita", "Pandram", "Ravali", "Chouhan", "Devi",
    "Hembram", "Ali", "Pandit", "Sarkar", "Kundu", "Gorai", "Jain", "Dubey",
]


def rand_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"


def rand_doj():
    start = date(2019, 1, 1)
    end = date(2025, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))


DESIGNATIONS_IC = [
    "CCE", "Tele Caller", "Customer Care Executive", "Apprentice-Customer Care",
    "Apprentice Customer Care", "FOS Executive", "Collection Executive",
    "Customer Relationship Executive", "Sr. CCE", "Sr. Customer Care Executive",
    "Senior Customer Service Executive",
]
DESIGNATIONS_TL = [
    "Team Lead", "Team Leader", "Team Manager", "Supervisor",
    "Lead - Operations", "Senior Officer", "Sr. Team Lead",
    "Senior Team Lead", "WFM Executive", "Lead Executive",
]
DESIGNATIONS_M1 = [
    "Assistant Manager", "Deputy Manager", "Manager", "Senior Manager",
    "WFM Exec", "Lead Exec", "General Manager", "Team Lead",
]
DESIGNATIONS_SR = [
    "Senior Manager", "General Manager", "Vice President",
    "Senior Vice President", "Director Operations", "AVP",
]

GRADES_IC   = ["A1.1", "A1.2", "A1.3", "PT", "AT", "NAPS", "NATS"]
GRADES_TL   = ["A2.1", "A2.2", "A3", "A4", "A5"]
GRADES_M1   = ["E1", "E2"]
GRADES_M2   = ["E3", "E4"]
GRADES_M3   = ["E5", "E6"]
GRADES_M4   = ["E7", "E8"]
GRADES_ALL_SR = GRADES_M1 + GRADES_M2 + GRADES_M3 + GRADES_M4

# OTC PA (annual, rupees) by grade band
OTC_PA_RANGE = {
    "IC":  (80_000,  180_000),
    "TL":  (150_000, 320_000),
    "M1":  (320_000, 600_000),
    "SR":  (600_000, 1_500_000),
}


def rand_otc_pa(grade: str) -> int:
    if grade in GRADES_IC:
        lo, hi = OTC_PA_RANGE["IC"]
    elif grade in GRADES_TL:
        lo, hi = OTC_PA_RANGE["TL"]
    elif grade in GRADES_M1:
        lo, hi = OTC_PA_RANGE["M1"]
    else:
        lo, hi = OTC_PA_RANGE["SR"]
    # round to nearest 100
    return round(random.randint(lo, hi) / 100) * 100


# Process / service-line mapping (matches app.py keys)
PROCESS_OPTIONS = [
    "CLM Domestic BFSI | Inbound",
    "CLM Domestic BFSI | Outbound",
    "CLM Domestic BFSI | Back office",
    "CLM Domestic Diversified | Inbound",
    "CLM Domestic Diversified | Outbound",
    "CLM Domestic Diversified | Back office",
    "CLM International | Inbound",
    "CLM International | Outbound",
    "CLM International | Back office",
    "Collections",
    "Collections | Telecollection",
    "Collections | FOS",
    "Delivery Assurance & Practices - BPM | Quality",
    "Delivery Assurance & Practices - BPM | WFM",
    "HR Operations | Onboarding",
    "Talent Acquisition | Recruiting",
    "CLM Domestic BFSI | Manpower - Back office",
    "CLM Domestic Diversified | Manpower - Back office",
]

SERVICE_LINE_MAP = {
    "CLM Domestic BFSI | Inbound":          "CLM",
    "CLM Domestic BFSI | Outbound":         "CLM",
    "CLM Domestic BFSI | Back office":      "Back Office & F&A",
    "CLM Domestic Diversified | Inbound":   "CLM",
    "CLM Domestic Diversified | Outbound":  "CLM",
    "CLM Domestic Diversified | Back office": "Back Office & F&A",
    "CLM International | Inbound":          "CLM",
    "CLM International | Outbound":         "CLM",
    "CLM International | Back office":      "Back Office & F&A",
    "Collections":                          "Collections",
    "Collections | Telecollection":         "Collections",
    "Collections | FOS":                    "Collections",
    "Delivery Assurance & Practices - BPM | Quality": "Delivery support",
    "Delivery Assurance & Practices - BPM | WFM":     "Delivery support",
    "HR Operations | Onboarding":           "Delivery support",
    "Talent Acquisition | Recruiting":      "Delivery support",
    "CLM Domestic BFSI | Manpower - Back office":       "Manpower",
    "CLM Domestic Diversified | Manpower - Back office": "Manpower",
}

CORE_DELIVERY_MAP = {
    "CLM":            "Core delivery",
    "Collections":    "Core delivery",
    "Back Office & F&A": "Core delivery",
    "Delivery support": "Delivery support",
    "Manpower":       "Manpower",
}

CLUSTERS = ["FGT", "Emerging", "Pvt", "NA"]

CUSTOMERS = [
    "SWIGGY", "FASHNEAR TECHNOLOGIES PRIVATE LIMITED",
    "TATA PLAY LIMITED", "SBI Cards", "PORTER LOGISTICS",
    "CHOLAMANDALAM INVESTMENT AND FT CORP",
    "TATA CAPITAL FINANCIAL SERVICES LIMITED",
    "MYNTRA DESIGN PRIVATE LIMITED",
    "HINDUJA HOUSING FINANCE COMPANY LIMITED",
    "TATA POWER COMPANY LIMITED", "IDFC FIRST BANK",
    "WHIZDOM INNOVATION PRIVATE LIMITED",
    "TATA MOTORS", "TATA STEEL",
]

LOCATIONS = [
    "Hyderabad", "Jamshedpur", "Kolkata", "Bengaluru", "Noida",
    "Mumbai", "Indore", "Chennai", "Bhadrak", "Mohal", "Ajmer",
    "Bellary", "Guwahati", "Sambalpur", "Keonihar",
]

COST_CENTERS = [
    ("40COTCHFOH",  "CLM Domestic BFSI"),
    ("40FSTCFSX3",  "CLM Domestic BFSI"),
    ("20KO01IB2",   "CLM Domestic Diversified"),
    ("40COTCFSSB",  "CLM Domestic BFSI"),
    ("CORPFIN1",    "Accounting"),
    ("40JAFTPVOI",  "CLM Domestic Diversified"),
    ("JAM02HR01",   "HRBP"),
    ("20JA01IBC",   "CLM Domestic Diversified"),
    ("40KOSSSLIOB", "CLM Domestic Diversified"),
    ("JAM02FCT1",   "Facilities"),
    ("40JATSLGPM",  "CLM Domestic Diversified"),
    ("40FSTMFLXB",  "Collections"),
    ("20KO01OBA",   "CLM Domestic Diversified"),
    ("LDA01HR01",   "Talent Acquisition"),
    ("KOL01FCT1",   "Facilities"),
    ("KOL01HR01",   "HRBP"),
    ("40KSACTCAM",  "CLM Domestic Diversified"),
    ("40RBSBITCO",  "CLM Domestic Diversified"),
    ("40ARTAIGCC",  "Collections"),
]

DIVISIONS = [
    "CLM Domestic BFSI", "CLM Domestic Diversified", "Collections",
    "Delivery Assurance & Practices - BPM", "HR Operations",
    "Talent Acquisition", "HRBP", "Facilities", "Accounting",
]

JOB_FUNCTIONS = [
    "Customer Service", "Administrative Services Generalist",
    "HR Generalist", "Customer Contact Center Training / Coaching",
]


def rand_grade_band():
    r = random.random()
    if r < 0.65:
        return "IC", random.choice(GRADES_IC)
    elif r < 0.85:
        return "TL", random.choice(GRADES_TL)
    elif r < 0.93:
        return "M1", random.choice(GRADES_M1)
    elif r < 0.97:
        return "M2", random.choice(GRADES_M2)
    elif r < 0.99:
        return "M3", random.choice(GRADES_M3)
    else:
        return "M4", random.choice(GRADES_M4)


def grade_desig(band: str) -> str:
    if band == "IC":
        return random.choice(DESIGNATIONS_IC)
    elif band == "TL":
        return random.choice(DESIGNATIONS_TL)
    else:
        return random.choice(DESIGNATIONS_M1)


# ─── HRMS snapshot (Images 1 + 2 structure) ───────────────────────────────────

def make_hrms_snapshot(n_total=250, prev_ids=None, prev_rows=None,
                       exits_n=10, hires_n=15, bu_label="Conneqt Business Solution"):
    """
    Produces a DataFrame matching the column structure visible in images 1+2:
      Employee ID | Grade | IC | TL | M1 | Name | Designation | OTC PA |
      Work Location | Country | Business | Business unit | Manager id | Check |
      Separation | Customer name | Core delivery/delivery support | Cluster |
      Classification | Manpower | PROCESS
    """
    rows: list[dict] = []
    name_cache: dict[str, str] = {}
    mgr_pool: list[tuple[str, str]] = []   # (id, name) of TL / M1 managers

    # ── CXO (4) ───────────────────────────────────────────────────────────────
    for _ in range(4):
        eid = rand_id()
        name = rand_name()
        name_cache[eid] = name
        rows.append({
            "Employee ID":   eid,
            "Grade":         "E6",
            "IC":            0, "TL": 0, "M1": 1,
            "Name":          name,
            "Designation":   "Vice President",
            "OTC PA":        rand_otc_pa("E6"),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "BPM - Practices & Ops",
            "Business unit": "CXO",
            "Manager id":    "",
            "Check":         1,
            "Separation":    0,
            "Customer name": "",
            "Core delivery/delivery support": "",
            "Cluster":       "NA",
            "Classification": "M1+",
            "Manpower":      0,
            "PROCESS":       "",
        })

    # ── Tech & Digital (15) ──────────────────────────────────────────────────
    for _ in range(15):
        band, grade = ("M1", "E2") if _ == 0 else ("IC", random.choice(["A3", "A4"]))
        eid = rand_id()
        name = rand_name()
        name_cache[eid] = name
        rows.append({
            "Employee ID":   eid,
            "Grade":         grade,
            "IC":            1 if band == "IC" else 0,
            "TL":            0, "M1": 1 if band == "M1" else 0,
            "Name":          name,
            "Designation":   grade_desig(band),
            "OTC PA":        rand_otc_pa(grade),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "Tech & Digital",
            "Business unit": "Tech & Digital",
            "Manager id":    "",
            "Check":         1,
            "Separation":    0,
            "Customer name": "",
            "Core delivery/delivery support": "",
            "Cluster":       "NA",
            "Classification": band,
            "Manpower":      0,
            "PROCESS":       "",
        })

    # ── Support Functions (20) ───────────────────────────────────────────────
    support_bus = [
        "Support Functions - HR", "Support Functions - Finance",
        "Support Functions - Administration", "Support Functions - IT",
    ]
    for sf_bu in support_bus:
        mgr_eid = rand_id()
        mgr_name = rand_name()
        name_cache[mgr_eid] = mgr_name
        mgr_pool.append((mgr_eid, mgr_name))
        rows.append({
            "Employee ID":   mgr_eid,
            "Grade":         "A5",
            "IC":            0, "TL": 1, "M1": 0,
            "Name":          mgr_name,
            "Designation":   "Manager",
            "OTC PA":        rand_otc_pa("A5"),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "HR" if "HR" in sf_bu else "Finance",
            "Business unit": sf_bu,
            "Manager id":    "",
            "Check":         1,
            "Separation":    0,
            "Customer name": "",
            "Core delivery/delivery support": "",
            "Cluster":       "NA",
            "Classification": "TL",
            "Manpower":      0,
            "PROCESS":       "",
        })
        for _ in range(4):
            eid = rand_id()
            name = rand_name()
            name_cache[eid] = name
            rows.append({
                "Employee ID":   eid,
                "Grade":         "A1.2",
                "IC":            1, "TL": 0, "M1": 0,
                "Name":          name,
                "Designation":   random.choice(DESIGNATIONS_IC),
                "OTC PA":        rand_otc_pa("A1.2"),
                "Work Location": random.choice(LOCATIONS),
                "Country":       "India",
                "Business":      "HR" if "HR" in sf_bu else "Finance",
                "Business unit": sf_bu,
                "Manager id":    mgr_eid,
                "Check":         1,
                "Separation":    0,
                "Customer name": "",
                "Core delivery/delivery support": "",
                "Cluster":       "NA",
                "Classification": "IC",
                "Manpower":      0,
                "PROCESS":       "",
            })

    # ── Alldigi (20) ─────────────────────────────────────────────────────────
    aldi_mgr_eid = rand_id()
    aldi_mgr_name = rand_name()
    name_cache[aldi_mgr_eid] = aldi_mgr_name
    mgr_pool.append((aldi_mgr_eid, aldi_mgr_name))
    rows.append({
        "Employee ID":   aldi_mgr_eid,
        "Grade":         "A3",
        "IC":            0, "TL": 1, "M1": 0,
        "Name":          aldi_mgr_name,
        "Designation":   "Team Lead",
        "OTC PA":        rand_otc_pa("A3"),
        "Work Location": random.choice(LOCATIONS),
        "Country":       "India",
        "Business":      "BPM - Practices & Ops",
        "Business unit": "Alldigi",
        "Manager id":    "",
        "Check":         1,
        "Separation":    0,
        "Customer name": random.choice(CUSTOMERS),
        "Core delivery/delivery support": "Core delivery",
        "Cluster":       random.choice(CLUSTERS),
        "Classification": "TL",
        "Manpower":      0,
        "PROCESS":       random.choice(PROCESS_OPTIONS),
    })
    for _ in range(19):
        eid = rand_id()
        name = rand_name()
        name_cache[eid] = name
        band, grade = "IC", random.choice(GRADES_IC)
        proc = random.choice(PROCESS_OPTIONS)
        sl = SERVICE_LINE_MAP.get(proc, "CLM")
        cd = CORE_DELIVERY_MAP.get(sl, "Core delivery")
        rows.append({
            "Employee ID":   eid,
            "Grade":         grade,
            "IC":            1, "TL": 0, "M1": 0,
            "Name":          name,
            "Designation":   grade_desig(band),
            "OTC PA":        rand_otc_pa(grade),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "BPM - Practices & Ops",
            "Business unit": "Alldigi",
            "Manager id":    aldi_mgr_eid,
            "Check":         1,
            "Separation":    0,
            "Customer name": random.choice(CUSTOMERS),
            "Core delivery/delivery support": cd,
            "Cluster":       random.choice(CLUSTERS),
            "Classification": "IC",
            "Manpower":      0,
            "PROCESS":       proc,
        })

    # ── Conneqt core delivery (fill to n_total) ───────────────────────────────
    conneqt_target = n_total - len(rows)

    # Carry-forward from previous snapshot
    carried: dict[str, dict] = {}
    if prev_ids and prev_rows:
        staying = list(prev_ids)
        random.shuffle(staying)
        for eid in staying[exits_n:]:
            if eid in prev_rows:
                carried[eid] = dict(prev_rows[eid])

    new_n = max(0, conneqt_target - len(carried))

    # M1+ managers
    m1_pool: list[tuple[str, str]] = []
    for _ in range(max(2, new_n // 40)):
        eid = rand_id()
        name = rand_name()
        name_cache[eid] = name
        m1_pool.append((eid, name))
        mgr_pool.append((eid, name))
        proc = random.choice(PROCESS_OPTIONS)
        sl = SERVICE_LINE_MAP.get(proc, "CLM")
        cd = CORE_DELIVERY_MAP.get(sl, "Core delivery")
        rows.append({
            "Employee ID":   eid,
            "Grade":         random.choice(GRADES_M1),
            "IC":            0, "TL": 0, "M1": 1,
            "Name":          name,
            "Designation":   random.choice(DESIGNATIONS_M1),
            "OTC PA":        rand_otc_pa(random.choice(GRADES_M1)),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "BPM - Practices & Ops",
            "Business unit": "Conneqt Business Solution",
            "Manager id":    "",
            "Check":         1,
            "Separation":    0,
            "Customer name": random.choice(CUSTOMERS),
            "Core delivery/delivery support": cd,
            "Cluster":       random.choice(CLUSTERS),
            "Classification": "M1+",
            "Manpower":      0,
            "PROCESS":       proc,
        })

    # TL managers
    tl_pool: list[tuple[str, str]] = []
    for _ in range(max(3, new_n // 10)):
        eid = rand_id()
        name = rand_name()
        name_cache[eid] = name
        tl_pool.append((eid, name))
        mgr_pool.append((eid, name))
        m_eid, m_name = random.choice(m1_pool) if m1_pool else ("", "")
        grade = random.choice(GRADES_TL)
        proc = random.choice(PROCESS_OPTIONS)
        sl = SERVICE_LINE_MAP.get(proc, "CLM")
        cd = CORE_DELIVERY_MAP.get(sl, "Core delivery")
        rows.append({
            "Employee ID":   eid,
            "Grade":         grade,
            "IC":            0, "TL": 1, "M1": 0,
            "Name":          name,
            "Designation":   grade_desig("TL"),
            "OTC PA":        rand_otc_pa(grade),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "BPM - Practices & Ops",
            "Business unit": "Conneqt Business Solution",
            "Manager id":    m_eid,
            "Check":         1,
            "Separation":    0,
            "Customer name": random.choice(CUSTOMERS),
            "Core delivery/delivery support": cd,
            "Cluster":       random.choice(CLUSTERS),
            "Classification": "TL",
            "Manpower":      0,
            "PROCESS":       proc,
        })

    # IC employees
    ic_n = new_n - len(m1_pool) - len(tl_pool)
    for _ in range(max(0, ic_n)):
        eid = rand_id()
        name = rand_name()
        name_cache[eid] = name
        t_eid, t_name = random.choice(tl_pool) if tl_pool else (random.choice(m1_pool) if m1_pool else ("", ""))
        grade = random.choice(GRADES_IC)
        proc = random.choice(PROCESS_OPTIONS)
        sl = SERVICE_LINE_MAP.get(proc, "CLM")
        cd = CORE_DELIVERY_MAP.get(sl, "Core delivery")
        is_manpower = 1 if sl == "Manpower" else 0
        rows.append({
            "Employee ID":   eid,
            "Grade":         grade,
            "IC":            1, "TL": 0, "M1": 0,
            "Name":          name,
            "Designation":   grade_desig("IC"),
            "OTC PA":        rand_otc_pa(grade),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "BPM - Practices & Ops",
            "Business unit": "Conneqt Business Solution",
            "Manager id":    t_eid,
            "Check":         1,
            "Separation":    0,
            "Customer name": random.choice(CUSTOMERS),
            "Core delivery/delivery support": cd,
            "Cluster":       random.choice(CLUSTERS),
            "Classification": "IC",
            "Manpower":      is_manpower,
            "PROCESS":       proc,
        })

    rows.extend(carried.values())

    # New hires
    for _ in range(hires_n):
        eid = rand_id()
        name = rand_name()
        name_cache[eid] = name
        t_eid, t_name = random.choice(tl_pool) if tl_pool else ("", "")
        grade = random.choice(GRADES_IC)
        proc = random.choice(PROCESS_OPTIONS)
        sl = SERVICE_LINE_MAP.get(proc, "CLM")
        cd = CORE_DELIVERY_MAP.get(sl, "Core delivery")
        rows.append({
            "Employee ID":   eid,
            "Grade":         grade,
            "IC":            1, "TL": 0, "M1": 0,
            "Name":          name,
            "Designation":   grade_desig("IC"),
            "OTC PA":        rand_otc_pa(grade),
            "Work Location": random.choice(LOCATIONS),
            "Country":       "India",
            "Business":      "BPM - Practices & Ops",
            "Business unit": "Conneqt Business Solution",
            "Manager id":    t_eid,
            "Check":         1,
            "Separation":    0,
            "Customer name": random.choice(CUSTOMERS),
            "Core delivery/delivery support": cd,
            "Cluster":       random.choice(CLUSTERS),
            "Classification": "IC",
            "Manpower":      0,
            "PROCESS":       proc,
        })

    df = pd.DataFrame(rows).drop_duplicates(subset=["Employee ID"])
    id_set = set(df["Employee ID"])
    row_dict = {r["Employee ID"]: r for r in df.to_dict("records")}
    return df, id_set, row_dict, name_cache


# ─── Conneqt analysis workbook (Images 3 + 4 structure) ───────────────────────

def make_conneqt_analysis(hrms_df: pd.DataFrame, base_hrms_df: pd.DataFrame | None = None,
                           spartan_ids: set | None = None) -> pd.DataFrame:
    """
    Produces a DataFrame matching images 3+4 column structure:
      Employee ID | Grade | Grade map | Name | Designation | OTC PA |
      Work Location | Country | Business | Business unit | Manager id | Check |
      Present in | Separation | Sept Salary | Diff in Sal | LWD |
      Spartan Category | Customer name | IC flag | TL flag | M1 flag |
      M2 Flag | M3 Flag | M4+ Flag | TL+ | Service line | PROCESS |
      COST CENTER | DIVISION | JOB_FUNCTION
    """
    spartan_ids = spartan_ids or set()
    rows = []

    # Grade map abbreviations (same as what appears in the image column C)
    grade_map_table = {
        "A1.1": "IC", "A1.2": "IC", "A1.3": "IC",
        "NAPS": "IC", "NATS": "IC", "PT": "IC", "AT": "IC",
        "A2.1": "TL", "A2.2": "TL", "A3": "TL", "A4": "TL", "A5": "TL",
        "E1": "M1", "E2": "M1",
        "E3": "M2", "E4": "M2",
        "E5": "M3", "E6": "M3",
        "E7": "M4+", "E8": "M4+",
        "P3": "M1", "P4": "M2",
    }

    for _, emp in hrms_df.iterrows():
        grade = str(emp.get("Grade", ""))
        gmap  = grade_map_table.get(grade, "IC")
        proc  = str(emp.get("PROCESS", ""))
        sl    = SERVICE_LINE_MAP.get(proc, "")
        eid   = str(emp.get("Employee ID", ""))
        otc   = emp.get("OTC PA", 0) or 0

        # Role flags from Classification / Grade
        ic_flag  = 1 if gmap == "IC"  else 0
        tl_flag  = 1 if gmap == "TL"  else 0
        m1_flag  = 1 if gmap == "M1"  else 0
        m2_flag  = 1 if gmap == "M2"  else 0
        m3_flag  = 1 if gmap == "M3"  else 0
        m4_flag  = 1 if gmap == "M4+" else 0
        tl_plus  = 1 if tl_flag or m1_flag or m2_flag or m3_flag or m4_flag else 0

        # Sept Salary (same as current OTC PA / 12 for monthly)
        sept_salary = round(otc / 12) if otc else 0

        # Diff in Sal vs base month (simulate small delta)
        base_otc = 0
        if base_hrms_df is not None:
            base_match = base_hrms_df[base_hrms_df["Employee ID"].astype(str) == eid]
            if not base_match.empty:
                base_otc = base_match.iloc[0].get("OTC PA", 0) or 0
        diff_sal = round((otc - base_otc) / 12) if base_otc else 0

        # LWD — only for spartan exits
        lwd = ""
        spartan_cat = ""
        present_in = 1
        if eid in spartan_ids:
            lwd_date = date(2026, 2, 1) + timedelta(days=random.randint(-30, 20))
            lwd = lwd_date.strftime("%-m/%-d/%Y")
            spartan_cat = random.choice(["Resigned", "Terminated", "Absconded"])
            present_in = 0

        # COST CENTER — pick based on division
        cc, division = random.choice(COST_CENTERS)

        rows.append({
            "Employee ID":     eid,
            "Grade":           grade,
            "Grade map":       gmap,
            "Name":            emp.get("Name", ""),
            "Designation":     emp.get("Designation", ""),
            "OTC PA":          otc,
            "Work Location":   emp.get("Work Location", ""),
            "Country":         "India",
            "Business":        emp.get("Business", ""),
            "Business unit":   emp.get("Business unit", ""),
            "Manager id":      emp.get("Manager id", ""),
            "Check":           emp.get("Check", 1),
            "Present in":      present_in,
            "Separation":      emp.get("Separation", 0),
            "Sept Salary":     sept_salary,
            "Diff in Sal":     diff_sal,
            "LWD":             lwd,
            "Spartan Category": spartan_cat,
            "Customer name":   emp.get("Customer name", ""),
            "IC flag":         ic_flag,
            "TL flag":         tl_flag,
            "M1 flag":         m1_flag,
            "M2 Flag":         m2_flag,
            "M3 Flag":         m3_flag,
            "M4+ Flag":        m4_flag,
            "TL+":             tl_plus,
            "Service line":    sl,
            "PROCESS":         proc,
            "COST CENTER":     cc,
            "DIVISION":        division,
            "JOB_FUNCTION":    random.choice(JOB_FUNCTIONS),
        })

    return pd.DataFrame(rows)


# ─── Spartan generator ────────────────────────────────────────────────────────

def make_spartan(exited_ids: list[str], names: dict[str, str], ref_date: date) -> pd.DataFrame:
    rows = []
    for eid in exited_ids:
        lwd = ref_date - timedelta(days=random.randint(5, 60))
        rows.append({
            "EMPLOYEE ID":      eid,
            "NAME":             names.get(eid, rand_name()),
            "SPARTAN CATEGORY": random.choice(["Resigned", "Terminated", "Absconded", "Retired"]),
            "LWD":              lwd.strftime("%Y-%m-%d"),
            "D3":               random.choice(["1", "1", "1", ""]),
        })
    return pd.DataFrame(rows)


# ─── Payroll generator ────────────────────────────────────────────────────────

def make_payroll(active_ids: set[str], names: dict[str, str]) -> pd.DataFrame:
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


# ─── Conneqt cost-code cluster mapping ───────────────────────────────────────

def make_conneqt_mapping() -> pd.DataFrame:
    rows = [{"Cost Code": cc, "Cluster": div} for cc, div in COST_CENTERS]
    return pd.DataFrame(rows)


# ─── save helper ──────────────────────────────────────────────────────────────

def save(df: pd.DataFrame, path: Path):
    df.to_excel(path, index=False)
    print(f"  ✓  {path.name}  ({len(df)} rows, {len(df.columns)} cols)")


# ─── main ─────────────────────────────────────────────────────────────────────

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

    all_names = {**names1, **names2, **names3}

    # Spartan — people who left between Jan and Feb
    exited_jan_to_feb = list(ids2 - ids3)[:20]
    spartan_df = make_spartan(exited_jan_to_feb, all_names, date(2026, 2, 28))
    save(spartan_df, OUT / "Spartan_D2_Feb2026.xlsx")

    # Payroll
    spartan_ids_in_payroll = set(exited_jan_to_feb[:3])
    payroll_df = make_payroll(ids3 | spartan_ids_in_payroll, all_names)
    save(payroll_df, OUT / "Payroll_Feb2026.xlsx")

    # Conneqt cost-code cluster mapping
    mapping_df = make_conneqt_mapping()
    save(mapping_df, OUT / "Conneqt_CostCode_Mapping.xlsx")

    # Conneqt analysis workbook (images 3+4 structure)
    # Uses Jan HRMS as "current" and Dec HRMS as "base" for salary diff
    conneqt_df = make_conneqt_analysis(
        hrms_df=df2,
        base_hrms_df=df1,
        spartan_ids=set(exited_jan_to_feb),
    )
    save(conneqt_df, OUT / "Conneqt_Jan_analysis_v4.xlsx")

    print(f"\nAll files written to: {OUT.resolve()}")
    print("\nUpload order in dashboard:")
    print("  HRMS files:    HRMS_2025_12_31.xlsx, HRMS_2026_01_31.xlsx, HRMS_2026_02_28.xlsx")
    print("  Spartan file:  Spartan_D2_Feb2026.xlsx")
    print("  Payroll file:  Payroll_Feb2026.xlsx")
    print("  Mapping file:  Conneqt_CostCode_Mapping.xlsx")
    print("  Analysis file: Conneqt_Jan_analysis_v4.xlsx  (reference / span pivot)")
    print("  Payroll cycle: 2026-02-01  →  2026-02-28")
    print()
    print("HRMS columns (images 1+2 structure):")
    for col in df2.columns:
        print(f"  • {col}")
    print()
    print("Conneqt analysis columns (images 3+4 structure):")
    for col in conneqt_df.columns:
        print(f"  • {col}")


if __name__ == "__main__":
    main()
