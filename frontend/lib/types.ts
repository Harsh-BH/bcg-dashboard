export interface SnapshotMeta {
  label: string;
  month_key: [number, number, number];
  file_name: string;
}

export interface TrendData {
  labels: string[];
  total: number[];
  delivery: number[];
  support: number[];
  cxo: number[];
}

export interface HierRow {
  label: string;
  rowtype: "grand" | "header" | "child";
  values: Record<string, number | string | null>;
}

export interface PairTableData {
  start_label: string;
  end_label: string;
  hier_rows: HierRow[];
}

export interface ReconciliationData {
  base_label: string;
  end_label: string;
  rows: Record<string, number | string | null>[];
  salary_rows?: Record<string, number | string | null>[];
}

export interface SpanData {
  unknown_grades: string[];
  trend_long: Record<string, unknown>[];
  service_line_counts: Record<string, unknown>[];
  service_line_span: Record<string, unknown>[];
  service_line_roles: Record<string, unknown>[];
  single_snapshot_label: string;
  single_snapshot_roles: Record<string, unknown>[];
  cluster_summary: Record<string, unknown>[];
  cluster_status: string;
}

export interface SpartanChecksData {
  spartan_available: boolean;
  spartan_report: { sheet_used: string; header_row: number } | null;
  spartan_exit_count: number;
  bau_attrition_count: number;
  new_hire_count: number;
  offenders_hrms: Record<string, unknown>[];
  offenders_hrms_count: number;
  overdue_spartan: Record<string, unknown>[];
  overdue_spartan_count: number;
  payroll: PayrollChecksData;
}

export interface PayrollChecksData {
  payroll_available: boolean;
  spartan_required?: boolean;
  payroll_cycle_start?: string;
  payroll_cycle_end?: string;
  payroll_count?: number;
  flagged_count?: number;
  flagged?: Record<string, unknown>[];
}

export interface ValidationWarning {
  file: string;
  message: string;
}

export interface ProcessResponse {
  session_id: string;
  snapshots: SnapshotMeta[];
  trend: TrendData;
  overview_table: OverviewRow[];
  pair_tables: Record<string, PairTableData>;
  reconciliation_tables: Record<string, ReconciliationData>;
  span: SpanData;
  spartan_checks: Record<string, SpartanChecksData>;
  validation_warnings: ValidationWarning[];
}

export interface DrillResponse {
  people: PersonRow[];
  total: number;
}

export interface OverviewRow {
  start_month: string;
  end_month: string;
  start_hc: number;
  end_hc: number;
  abs_change: number;
  pct_change: number | null;
  pct_change_delivery: number | null;
  pct_change_cxo: number | null;
  pct_change_support: number | null;
}

export type PersonRow = Record<string, unknown>;

// ── AI Feature Types ─────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: number;
}

export type AnomalyTab = "overall" | "hrms-walk" | "span" | "spartan";
export type AnomalySeverity = "high" | "medium" | "low";

export interface Anomaly {
  tab: AnomalyTab;
  severity: AnomalySeverity;
  title: string;
  explanation: string;
}

export interface ColumnMapping {
  original: string;
  suggested: string;
  confirmed: boolean;
}

export interface ValidationResult {
  missing: string[];          // truly mandatory columns absent → blocks processing
  recommended: string[];      // optional but functional columns absent → amber warning
  mappings: ColumnMapping[];
  valid: boolean;
}
