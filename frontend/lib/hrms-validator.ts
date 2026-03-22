import * as XLSX from "xlsx";
import type { ColumnMapping, ValidationResult } from "@/lib/types";

// Required HRMS columns (from backend normalization logic)
const REQUIRED_COLUMNS = [
  "EMPLOYEE ID",
  "EMPLOYEE NAME",
  "DESIGNATION",
  "GRADE",
  "PROCESS",
  "DEPARTMENT",
  "EMPLOYEE TYPE",
  "DATE OF JOINING",
];

// Aliases that are commonly seen in practice
const ALIASES: Record<string, string[]> = {
  "EMPLOYEE ID":   ["EMP ID", "EMP_ID", "EMPID", "EMPLOYEE_ID", "STAFF ID", "STAFF_ID"],
  "EMPLOYEE NAME": ["EMP NAME", "EMP_NAME", "NAME", "FULL NAME", "FULL_NAME", "EMPLOYEE_NAME"],
  "DESIGNATION":   ["DESIG", "DESIGNATION_NAME", "ROLE", "POSITION"],
  "GRADE":         ["GRADE CODE", "GRADE_CODE", "GRADE BAND", "BAND"],
  "PROCESS":       ["PROCESS NAME", "PROCESS_NAME", "DEPARTMENT PROCESS"],
  "DEPARTMENT":    ["DEPT", "DEPT_NAME", "DEPARTMENT_NAME", "DIVISION", "DIV", "DEPT NAME", "DEPARTMENT NAME", "VERTICAL"],
  "EMPLOYEE TYPE": ["EMP TYPE", "EMP_TYPE", "EMPLOYMENT TYPE", "EMPLOYMENT_TYPE", "TYPE", "WORKER TYPE", "WORKER_TYPE"],
  "DATE OF JOINING": ["DOJ", "JOINING DATE", "JOIN DATE", "DATE_OF_JOINING", "DATE JOINED", "JOINING_DATE", "JOIN_DATE", "DOJ DATE"],
};

/** Levenshtein distance (case-insensitive) */
function levenshtein(a: string, b: string): number {
  const al = a.toLowerCase(), bl = b.toLowerCase();
  const m = al.length, n = bl.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  );
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = al[i - 1] === bl[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
  return dp[m][n];
}

function findBestMatch(col: string, candidates: string[]): string | null {
  const normalized = col.trim().toUpperCase();
  for (const req of REQUIRED_COLUMNS) {
    // Exact match
    if (normalized === req) return req;
    // Alias match
    if (ALIASES[req]?.some((a) => a.toUpperCase() === normalized)) return req;
    // Fuzzy match (distance ≤ 2)
    if (levenshtein(normalized, req) <= 2) return req;
  }
  return null;
}

export async function validateHrmsHeaders(file: File): Promise<ValidationResult> {
  const buffer = await file.arrayBuffer();
  const wb = XLSX.read(buffer, { sheetRows: 3 }); // read only first 3 rows
  const ws = wb.Sheets[wb.SheetNames[0]];
  const rows = XLSX.utils.sheet_to_json<string[]>(ws, { header: 1 });

  // Find the header row (first row with ≥ 3 non-empty string cells)
  let headerRow: string[] = [];
  for (const row of rows) {
    const cells = row.filter((c) => typeof c === "string" && c.trim().length > 0);
    if (cells.length >= 3) { headerRow = row.map((c) => String(c ?? "").trim().toUpperCase()); break; }
  }

  if (!headerRow.length) {
    return { missing: REQUIRED_COLUMNS, mappings: [], valid: false };
  }

  const mappings: ColumnMapping[] = [];
  const foundRequired = new Set<string>();

  // Check each detected column for matches
  for (const col of headerRow) {
    if (!col) continue;
    const match = findBestMatch(col, REQUIRED_COLUMNS);
    if (match && col !== match) {
      mappings.push({ original: col, suggested: match, confirmed: false });
      foundRequired.add(match);
    } else if (match) {
      foundRequired.add(match);
    }
  }

  const missing = REQUIRED_COLUMNS.filter((r) => !foundRequired.has(r));

  return {
    missing,
    mappings,
    valid: missing.length === 0,
  };
}
