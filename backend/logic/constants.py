import re

HR_MANDATORY_STD = [
    "EMPLOYEE ID",
    "ASSIGNMENT NUMBER",
    "NAME",
    "DATE OF JOINING",
    "EMPLOYEE TYPE",
    "LEVEL",
    "DESIGNATION",
    "BILLABLE NON BILLABLE",
    "WORK LOCATION",
    "STATE",
    "REGION",
    "COUNTRY",
    "EMPLOYEE STATUS",
    "EMPLOYMENT TYPE",
    "BUSINESS UNIT",
    "BUSINESS",
    "DIVISION",
    "PROCESS",
    "SUB PROCESS",
    "ORGANIZATION TYPE",
    "JOB FUNCTION",
    "SUB FUNCTION",
    "JOB FAMILY",
    "SUB FAMILY",
    "COST CENTER",
    "COST CENTER NAME",
    "MANAGER1 ECODE",
    "MANAGER1 EMPNAME",
]

BUCKET_CONNEQT = "Conneqt Business Solution"
BUCKET_ALLDIGI = "Alldigi"
BUCKET_TECHDIG = "Tech & Digital"
BUCKET_CXO = "CXO"
SUPPORT_PREFIX = "Support Functions - "

TECH_DIGITAL_BUSINESS = {"tech & digital", "ai, data & analytics"}
BPM_BUSINESS = "bpm - practices & ops"
VERTICAL_BUSINESS = "vertical"
HR_BUSINESS = {"hr", "communication"}

CXO_CODES_TYPE2 = {"CXO", "CX1", "CX2", "CX3"}

HR_FILE_RE = re.compile(
    r"^HRMS_(\d{4})_(0[1-9]|1[0-2])_(0[1-9]|[12]\d|3[01])\.xlsx$",
    re.IGNORECASE,
)

# Span grade sets
SPAN_GRADES_IC = {"naps", "nats", "pt", "at", "a1.1", "a1.2", "a1.3"}
SPAN_GRADES_TL = {"a3", "a4", "a5", "e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8"}

SPAN_TL_DESIGNATIONS = {
    "team lead",
    "team leader",
    "team manager",
    "senior manager",
    "senior manager quality",
    "senior officer",
    "lead",
    "srtl",
    "supervisor",
}

# Service line
SPAN_SL_CORE_KEYS = ("core_collections", "core_clm", "core_fa_back_office")

SPAN_SERVICE_LINE_ROW_SPEC: tuple[tuple[str, str, str | None], ...] = (
    ("Core Delivery", "Collections", "core_collections"),
    ("Core Delivery", "CLM", "core_clm"),
    ("Core Delivery", "F&A & back office", "core_fa_back_office"),
    ("Core Delivery", "Sub-total", None),
    ("Delivery support", "Quality", "ds_quality"),
    ("Delivery support", "Training", "ds_training"),
    ("Delivery support", "WFM", "ds_wfm"),
    ("Delivery support", "Others", "ds_others"),
    ("Delivery support", "Unclassified (PROCESS mapping TBD)", "unclassified"),
)

_SPAN_SERVICE_LINE_RULES_VERSION = 10

SPAN_SL_CC_OVERRIDE: dict[str, str] = {
    "40FSHBLAG1": "core_fa_back_office",
    "40FSHBLAGR": "core_collections",
    "40FSHBLTW1": "core_collections",
    "40FSHBLMAN": "core_collections",
    "40LDHBLAGR": "core_collections",
    "40FSHDFALC": "core_collections",
    "40KOSBITCO": "core_clm",
    "40RBSBITCO": "core_clm",
    "40KOSBITC1": "core_collections",
    "40ARTAIGCC": "core_clm",
    "40ARTAIGOB": "core_clm",
    "90PU2CROMA": "core_clm",
    "13HYATLDTH": "core_clm",
    "90HYATELBO": "core_clm",
    "40COMFCVOI": "core_clm",
    "40KSGHFBLO": "core_clm",
    "40KSGHFLCC": "core_clm",
    "40CH2MFLBO": "core_fa_back_office",
    "40KSGHFLBO": "core_fa_back_office",
    "40ARGHFL2E": "core_fa_back_office",
    "40KSGHFINV": "core_fa_back_office",
    "40KONABPLM": "core_collections",
    "40HYMMFCPC": "core_fa_back_office",
    "40LDJLRPO": "core_fa_back_office",
    "40LDJLRAP": "core_fa_back_office",
    "40KSTCFSPD": "core_fa_back_office",
    "40COTCSSAP": "core_fa_back_office",
    "40KSKSFBOF": "core_fa_back_office",
}

DIVISION_CLM_WHEN_PROCESS_BLANK: frozenset[str] = frozenset(
    {
        "customer service",
        "clm domestic bfsi",
        "clm domestic diversified",
        "customer contact center generalist",
        "customer contact center training / coaching",
    }
)

COLLECTIONS_DESIG_TOKENS: tuple[str, ...] = (
    "collection",
    "collections",
    "coll - exe",
    "customer relationship executive",
    "fos",
    "tele caller",
)

BACKOFFICE_DESIG_TOKENS: tuple[str, ...] = (
    "accounts",
    "finance",
    "shared service",
)

DS_OTHERS_DESIG_TOKENS: tuple[str, ...] = (
    "director operations",
    "vice president",
    "senior vice president",
)

CLM_GENERIC_DESIG_TOKENS: tuple[str, ...] = (
    "executive",
    "operations executive",
    "customer care executive",
    "cce",
    "ops - exe",
)

# Support bucket normalization
ADMIN_BUCKET_VARIANTS_TO_COLLAPSE = {
    "support functions - administration",
    "support functions - adminstration",
}
