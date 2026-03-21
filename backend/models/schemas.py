from typing import Any
from pydantic import BaseModel


class SnapshotMeta(BaseModel):
    label: str
    month_key: list[int]  # [year, month, day]
    file_name: str


class TrendData(BaseModel):
    labels: list[str]
    total: list[int]
    delivery: list[int]
    support: list[int]
    cxo: list[int]


class HierRow(BaseModel):
    label: str
    rowtype: str  # "grand" | "header" | "child"
    values: dict[str, Any]  # col_name -> value


class PairTableData(BaseModel):
    start_label: str
    end_label: str
    hier_rows: list[HierRow]
    # pre-computed people lists keyed by bucket name
    start_people: dict[str, list[dict]]
    end_people: dict[str, list[dict]]


class ReconciliationData(BaseModel):
    base_label: str
    end_label: str
    rows: list[dict]  # same shape as HierRow but 5 count columns
    # people lists for each of the 5 clickable columns keyed by bucket
    baseline_people: dict[str, list[dict]]
    spartan_exit_people: dict[str, list[dict]]
    bau_attrition_people: dict[str, list[dict]]
    new_hire_people: dict[str, list[dict]]
    end_people: dict[str, list[dict]]


class SpanData(BaseModel):
    unknown_grades: list[str]
    # trend table (long format): list of row dicts
    trend_long: list[dict]
    # service line wide tables
    service_line_counts: list[dict]
    service_line_span: list[dict]
    service_line_roles: list[dict]
    # single snapshot detail (last snapshot by default)
    single_snapshot_label: str
    single_snapshot_roles: list[dict]  # rows with IC/TL/M1+ column
    cluster_summary: list[dict]
    cluster_status: str


class SpartanChecksData(BaseModel):
    spartan_available: bool
    spartan_report: dict | None
    spartan_exit_count: int
    bau_attrition_count: int
    new_hire_count: int
    offenders_hrms: list[dict]
    offenders_hrms_count: int
    overdue_spartan: list[dict]
    overdue_spartan_count: int
    payroll: dict  # result of build_payroll_checks


class ValidationWarning(BaseModel):
    file: str
    message: str


class ProcessResponse(BaseModel):
    snapshots: list[SnapshotMeta]
    trend: TrendData
    overview_table: list[dict]
    pair_tables: dict[str, PairTableData]   # key: "label1 → label2"
    reconciliation_tables: dict[str, ReconciliationData]
    span: SpanData
    spartan_checks: dict[str, SpartanChecksData]  # key: "label1 → label2"
    validation_warnings: list[ValidationWarning]
