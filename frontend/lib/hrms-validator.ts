import * as XLSX from "xlsx";
import type { ValidationResult } from "@/lib/types";

// Required HRMS columns (must match backend HR_MANDATORY_STD after soft normalization)
const REQUIRED_COLUMNS = [
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
];

// Aliases for common variations (no underscore variants needed — normalizeCol handles those)
const ALIASES: Record<string, string[]> = {
  "EMPLOYEE ID":          ["EMP ID", "EMPID", "EMPLOYEE CODE", "EMPLOYEE NO", "EMPLOYEE NUMBER"],
  "ASSIGNMENT NUMBER":    ["ASSIGNMENT NO", "ASSIGN NUMBER", "ASSIGN NO"],
  "NAME":                 ["EMPLOYEE NAME", "EMP NAME", "FULL NAME"],
  "DATE OF JOINING":      ["DOJ", "JOINING DATE", "JOIN DATE"],
  "EMPLOYEE TYPE":        ["EMP TYPE"],
  "LEVEL":                ["EMPLOYEE LEVEL"],
  "DESIGNATION":          ["DESIG", "DESIGNATION NAME", "ROLE", "TITLE"],
  "BILLABLE NON BILLABLE":["BILLABLE NON-BILLABLE", "BILLABLE/NON BILLABLE", "BILLED NON BILLED", "BILLABLE"],
  "WORK LOCATION":        ["WORKLOCATION", "OFFICE LOCATION", "LOCATION"],
  "STATE":                ["EMP STATE"],
  "REGION":               ["EMP REGION"],
  "COUNTRY":              ["EMP COUNTRY"],
  "EMPLOYEE STATUS":      ["EMP STATUS", "EMPLOYMENT STATUS"],
  "EMPLOYMENT TYPE":      ["CONTRACT TYPE"],
  "BUSINESS UNIT":        ["BU"],
  "BUSINESS":             [],
  "DIVISION":             ["EMP DIVISION", "DIVISION NAME", "DIV"],
  "PROCESS":              ["PROCESS NAME"],
  "SUB PROCESS":          ["SUBPROCESS"],
  "ORGANIZATION TYPE":    ["ORG TYPE", "ORGANISATION TYPE"],
  "JOB FUNCTION":         ["JOBFUNCTION", "FUNCTION", "JOB ROLE"],
  "SUB FUNCTION":         ["SUBFUNCTION"],
  "JOB FAMILY":           ["JOBFAMILY"],
  "SUB FAMILY":           ["SUBFAMILY"],
  "COST CENTER":          ["COSTCENTER", "COST CENTRE", "CC"],
  "COST CENTER NAME":     ["COSTCENTERNAME", "COST CENTRE NAME"],
  "MANAGER1 ECODE":       ["MANAGER ECODE", "REPORTING MANAGER ID", "MANAGER ID"],
  "MANAGER1 EMPNAME":     ["MANAGER EMPNAME", "REPORTING MANAGER NAME", "MANAGER NAME"],
};

/** Normalize a column name: uppercase, collapse whitespace, replace _/- with space. */
function normalizeCol(s: string): string {
  return s.trim().toUpperCase().replace(/[_\-]/g, " ").replace(/\s+/g, " ");
}

/** Levenshtein distance between two already-normalized strings. */
function levenshtein(a: string, b: string): number {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  );
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
  return dp[m][n];
}

/**
 * Match a single file column against required columns using three ordered passes:
 *   1. Exact match (after normalizing underscores/hyphens/case)
 *   2. Alias match
 *   3. Fuzzy match (distance ≤ 1 only, to avoid SUB FAMILY ↔ JOB FAMILY collisions)
 *
 * Already-matched required columns are skipped so each required col is claimed once.
 */
function findMatch(norm: string, claimed: Set<string>): string | null {
  // Pass 1 — exact
  for (const req of REQUIRED_COLUMNS) {
    if (claimed.has(req)) continue;
    if (norm === req) return req;
  }
  // Pass 2 — alias
  for (const req of REQUIRED_COLUMNS) {
    if (claimed.has(req)) continue;
    if (ALIASES[req]?.some((a) => normalizeCol(a) === norm)) return req;
  }
  // Pass 3 — fuzzy (distance ≤ 1 only to stay conservative)
  for (const req of REQUIRED_COLUMNS) {
    if (claimed.has(req)) continue;
    if (levenshtein(norm, req) <= 1) return req;
  }
  return null;
}

export async function validateHrmsHeaders(file: File): Promise<ValidationResult> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { sheetRows: 3 });
  const ws = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json<string[]>(ws, { header: 1 });

  // Find first header-like row (≥ 3 non-empty string cells)
  let headerRow: string[] = [];
  for (const row of rows) {
    const cells = row.filter((c) => typeof c === "string" && c.trim().length > 0);
    if (cells.length >= 3) {
      headerRow = row.map((c) => String(c ?? "").trim());
      break;
    }
  }

  if (!headerRow.length) {
    return { missing: REQUIRED_COLUMNS, mappings: [], valid: false };
  }

  const claimed = new Set<string>();

  for (const col of headerRow) {
    if (!col) continue;
    const norm  = normalizeCol(col);
    const match = findMatch(norm, claimed);
    if (match) claimed.add(match);
  }

  const missing = REQUIRED_COLUMNS.filter((r) => !claimed.has(r));
  return { missing, mappings: [], valid: missing.length === 0 };
}
