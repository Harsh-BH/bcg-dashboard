from __future__ import annotations
import re

# Only 3 columns are truly mandatory — everything else is optional/derived
HR_MANDATORY_STD = ["EMPLOYEE ID", "BUSINESS UNIT", "BUSINESS"]

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

# TL designation phrases (A1.x / A2.x mandatory TL — space-insensitive substring)
# "senior manager", "senior manager quality", "senior officer", "srtl" removed per request
SPAN_TL_DESIGNATIONS = {
    "team lead",
    "team leader",
    "team manager",
    "lead",
    "supervisor",
}

# September-specific extra TL designation phrases (Collections/CLM/WFM/Quality/Training + MEU cluster)
SEPTEMBER_TL_EXTRA_PHRASES_SL_KEYS: frozenset[str] = frozenset(
    {"core_collections", "core_clm", "ds_wfm", "ds_quality", "ds_training"}
)
SEPTEMBER_TL_EXTRA_PHRASES_CLUSTER_NAMES: frozenset[str] = frozenset({"MEU"})
SEPTEMBER_TL_EXTRA_PHRASES: frozenset[str] = frozenset({
    "manager", "deputy manager", "lead", "supervisor",
    "admin manager", "assistant vp", "associate test lead",
    "sr. fos collections executive",
})
SEPTEMBER_TL_COLLECTIONS_CLM_PHRASES: frozenset[str] = frozenset(SEPTEMBER_TL_EXTRA_PHRASES)

# MEU September ONLY: these designation substrings override TL
SEPTEMBER_MEU_NON_TL_DESIGNATIONS: frozenset[str] = frozenset({"senior", "sr."})

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

_SPAN_SERVICE_LINE_RULES_VERSION = 44

# Exact process sets
CLM_VOICE_PROCESS: frozenset[str] = frozenset({
    "clm domestic bfsi | inbound",
    "clm domestic bfsi | outbound",
    "clm domestic diversified | inbound",
    "clm domestic diversified | outbound",
    "clm international | inbound",
    "clm international | outbound",
    "collections | fos",
})

CLM_BACKOFFICE_PROCESS: frozenset[str] = frozenset({
    "clm domestic bfsi | back office",
    "clm domestic diversified | back office",
    "clm international | back office",
})

COLLECTIONS_PROCESS: frozenset[str] = frozenset({
    "collections",
    "collections | telecollection",
})

# F&A back office exact processes (same as CLM_BACKOFFICE_PROCESS)
JAN_BO_PROCESSES: frozenset[str] = frozenset(CLM_BACKOFFICE_PROCESS)

# Dec-style CC overrides
DEC_CLM_BACKOFFICE_TO_BACKOFFICE_CC: frozenset[str] = frozenset({
    "40CH2MFLBO", "40COTCHFHL", "40COTCFSHB", "40HYMMFCPC", "40HYIDFCBO",
    "90KOTSLSSS", "40ARGHFL2E", "40LDCIIPCT", "40KSGHFLBO", "40NOITCLTW",
    "40COTCHFOH", "40KSGHFINV", "40COTCFSSB", "40COTCSSAP", "40KKTCLCPC",
    "40LDJLRAP", "40COTCSHLP", "40NO2TCHDH", "40COTCHFHB", "40LDTCFSPF",
    "90PU3BALCP", "40LDIPLIHR", "40COMACLSM", "40KSACTCAM", "40KSTCLCPC",
    "40KSNDHFBO", "40KSKSFBOF",
})

DEC_CLM_BACKOFFICE_TO_COLLECTIONS_CC: frozenset[str] = frozenset({
    "40KONABPLM", "40KVTMFLWC", "40LDHSLIOB", "40RBPCHFTC",
})

DEC_COLLECTIONS_TO_CLM_CC: frozenset[str] = frozenset({
    "13HYATLDTH", "20KO01OBA", "40AR2CBKVO", "40AR2SSBMP", "40AR4WENVO",
    "40ARTAIGCC", "40ARTAIGOB", "40BAKBLIOB", "40BAKBLSOB", "40CHIOBVOI",
    "40CORRLCSA", "40COUCOVOI", "40COUSFVOI", "40HY1FTPSS", "40HYCGGVOI",
    "40INMDLVOI", "40INUPGOBS", "40KOIPPBV1", "40KOSBITCO", "40KVKMBCOC",
    "40KVKMBETB", "40KVKMBPLO", "40KVOSCVOI", "40LDLDPLCC", "40LDRWLOBS",
    "40NO2AFSOS", "40RBMCOVOI", "40RBPCHFOS", "40RBRLBVOI", "40RBRLBVOP",
    "40RBSBITCO", "40RBSGIOBR", "90BA03TVSM", "90HYATELBO", "90MO01SBCC",
    "90PU02OB1", "90PU2CROMA",
})

DEC_COLLECTIONS_TO_BACKOFFICE_CC: frozenset[str] = frozenset({
    "40FSHBLAG1",
})

DEC_CLMVOICE_TO_COLLECTIONS_CC: frozenset[str] = frozenset({
    "40AR4PCHDT", "40ARCFLCC", "40ARIDFCTC", "40ARTVSMPC", "40BAMFLVOI",
    "40FSDFSCOL", "40FSLTFTWC", "40FSMMFXTC", "40KOCBITEL", "40KOSBITC1",
    "40KSTMFLIC", "40KVDHFCOL", "40LDCMFLOT", "40LDHSLIOB", "40NOMMFXTC",
    "40RBMMFXTC", "40RBPCHFTC", "40RBTVSTEC", "40RBTYCTCO", "90AR2MRHTC",
    "90ARIIBWOP", "90CHHHFCOL", "90PU02TFOS",
})

DEC_CLM_TO_DS_OTHERS_CC: frozenset[str] = frozenset({
    "LDA01HR01", "MOH01HR01", "CORPHRNAPS",
})

DEC_FORCE_UNCLASSIFIED_CC: frozenset[str] = frozenset({
    "NOT_LOADED", "09. Projects Department", "90HY01MEA1", "40N02AFSOS",
})

BLANK_PROCESS_TO_DS_OTHERS_CC: frozenset[str] = frozenset({
    "LDA01HR01", "MOH01HR01", "CORPHRNAPS", "CORPOPSEXC",
})

BLANK_PROCESS_TO_DS_OTHERS_ACCOUNT: frozenset[str] = frozenset({
    "human resource support", "operations excellence",
})

FORCE_UNCLASSIFIED_CC: frozenset[str] = frozenset({"NOT_LOADED", "09. Projects Department"})
FORCE_UNCLASSIFIED_ACCOUNT: frozenset[str] = frozenset({"not found"})

# Post-adjustment clusters
SPAN_ADJUST_CLUSTERS_MAR16_23: frozenset[str] = frozenset({"EMERGING"})

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
