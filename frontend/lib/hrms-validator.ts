import * as XLSX from "xlsx";
import type { ValidationResult } from "@/lib/types";

// Truly mandatory columns — matches backend HR_MANDATORY_STD (app.py ensure_cols).
// Everything else is optional; backend uses `if "X" in df.columns` guards.
const REQUIRED_COLUMNS = [
  "EMPLOYEE ID",
  "BUSINESS UNIT",
  "BUSINESS",
];

// Recommended columns — used by backend logic but backend handles absence gracefully.
// Shown as warnings (amber), not errors, so users know what improves functionality.
export const RECOMMENDED_COLUMNS = [
  "EMPLOYEE TYPE",   // filters to C/E employees
  "GRADE",           // span IC/TL/M1+ classification
  "LEVEL",           // span classification fallback
  "DESIGNATION",     // span TL designation matching
  "MANAGER1 ECODE",  // span hierarchy / reportee count
  "SEPARATION",      // filters out separated employees
  "OTC PA",          // salary walk (OTC PA → ₹ Cr)
  "PROCESS",         // service line classification
  "COST CENTER",     // cluster mapping
  "DIVISION",        // service line sub-classification
  "JOB FUNCTION",    // service line sub-classification
  "ACCOUNT NAME",    // account-wise span tables
];

// Aliases for common variations (normalizeCol already handles _ → space, lowercasing).
// ACCOUNT NAME and CUSTOMER NAME are the SAME field — if either is present it counts.
const ALIASES: Record<string, string[]> = {
  // ── Required ──────────────────────────────────────────────────────────────
  "EMPLOYEE ID":           ["EMP ID", "EMPID", "EMPLOYEE CODE", "EMPLOYEE NO", "EMPLOYEE NUMBER"],
  "BUSINESS UNIT":         ["BU"],
  "BUSINESS":              [],
  // ── Recommended ───────────────────────────────────────────────────────────
  "EMPLOYEE TYPE":         ["EMP TYPE"],
  "GRADE":                 ["EMPLOYEE GRADE", "EMP GRADE"],
  "LEVEL":                 ["EMPLOYEE LEVEL"],
  "DESIGNATION":           ["DESIG", "DESIGNATION NAME", "ROLE", "TITLE"],
  "MANAGER1 ECODE":        ["MANAGER ECODE", "REPORTING MANAGER ID", "REPORTING MANAGER", "MANAGER ID", "MANAGER EMP ID", "MANAGER EMPLOYEE ID"],
  "SEPARATION":            ["SEPARATIONS", "SEPARATION STATUS"],
  "OTC PA":                ["OTC P.A", "OTC/PA", "OTCPA"],
  "PROCESS":               ["PROCESS NAME", "PROCESS DESCRIPTION"],
  "COST CENTER":           ["COSTCENTER", "COST CENTRE", "CC", "COST CENTRE CODE"],
  "DIVISION":              ["EMP DIVISION", "DIVISION NAME", "DIV"],
  "JOB FUNCTION":          ["JOBFUNCTION", "FUNCTION", "JOB ROLE", "JOB FUNCTION NAME", "EMPLOYEE JOB FUNCTION"],
  // ACCOUNT NAME and CUSTOMER NAME are the same field — accept either header
  "ACCOUNT NAME":          ["CUSTOMER NAME", "CLIENT NAME", "CUSTOMER", "ACCOUNT"],
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
    return { missing: REQUIRED_COLUMNS, recommended: RECOMMENDED_COLUMNS, mappings: [], valid: false };
  }

  // Build a combined set of all columns to match against (required + recommended)
  const ALL_COLUMNS = [...REQUIRED_COLUMNS, ...RECOMMENDED_COLUMNS];
  const claimed = new Set<string>();

  for (const col of headerRow) {
    if (!col) continue;
    const norm = normalizeCol(col);
    // Pass 1 — exact
    for (const req of ALL_COLUMNS) {
      if (claimed.has(req)) continue;
      if (norm === req) { claimed.add(req); break; }
    }
    if (claimed.has(normalizeCol(col))) continue;
    // Pass 2 — alias
    for (const req of ALL_COLUMNS) {
      if (claimed.has(req)) continue;
      if (ALIASES[req]?.some((a) => normalizeCol(a) === norm)) { claimed.add(req); break; }
    }
    // Pass 3 — fuzzy (distance ≤ 1)
    for (const req of ALL_COLUMNS) {
      if (claimed.has(req)) continue;
      if (levenshtein(norm, req) <= 1) { claimed.add(req); break; }
    }
  }

  const missing     = REQUIRED_COLUMNS.filter((r) => !claimed.has(r));
  const recommended = RECOMMENDED_COLUMNS.filter((r) => !claimed.has(r));
  return { missing, recommended, mappings: [], valid: missing.length === 0 };
}
