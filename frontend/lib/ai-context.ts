import type { ProcessResponse } from "@/lib/types";

/**
 * Compresses the full ProcessResponse into a compact text summary
 * suitable for Claude's context window (~4-6k tokens max).
 * Strips large people arrays; keeps scalar summaries.
 */
export function buildDashboardContext(data: ProcessResponse): string {
  const lines: string[] = [];

  // ── Snapshots ─────────────────────────────────────────────────────────────
  const labels = data.snapshots.map((s) => s.label);
  lines.push(`## Snapshots (${labels.length} total)`);
  lines.push(labels.join(", "));

  // ── Trend ─────────────────────────────────────────────────────────────────
  lines.push("\n## Headcount Trend");
  lines.push("Month | Total | Delivery | Support | CXO");
  data.trend.labels.forEach((label, i) => {
    lines.push(
      `${label} | ${data.trend.total[i]} | ${data.trend.delivery[i]} | ${data.trend.support[i]} | ${data.trend.cxo[i]}`
    );
  });

  // ── MoM Overview ──────────────────────────────────────────────────────────
  lines.push("\n## Month-over-Month Overview");
  lines.push("Period | Start HC | End HC | Change | %Change | %Delivery | %Support | %CXO");
  data.overview_table.forEach((r) => {
    lines.push(
      `${r.start_month}→${r.end_month} | ${r.start_hc} | ${r.end_hc} | ${r.abs_change >= 0 ? "+" : ""}${r.abs_change} | ${r.pct_change != null ? r.pct_change.toFixed(1) + "%" : "N/A"} | ${r.pct_change_delivery != null ? r.pct_change_delivery.toFixed(1) + "%" : "N/A"} | ${r.pct_change_support != null ? r.pct_change_support.toFixed(1) + "%" : "N/A"} | ${r.pct_change_cxo != null ? r.pct_change_cxo.toFixed(1) + "%" : "N/A"}`
    );
  });

  // ── Reconciliation summaries ───────────────────────────────────────────────
  if (Object.keys(data.reconciliation_tables).length > 0) {
    lines.push("\n## Reconciliation Summaries (per period)");
    for (const [key, rec] of Object.entries(data.reconciliation_tables)) {
      lines.push(`\n### ${key}`);
      // Only include scalar rows (not people arrays which are huge)
      rec.rows.forEach((row) => {
        const rowStr = Object.entries(row)
          .filter(([, v]) => typeof v === "number" || typeof v === "string")
          .map(([k, v]) => `${k}: ${v}`)
          .join(", ");
        if (rowStr) lines.push(rowStr);
      });
    }
  }

  // ── Spartan checks ────────────────────────────────────────────────────────
  if (Object.keys(data.spartan_checks).length > 0) {
    lines.push("\n## Spartan/HRMS Checks");
    for (const [key, sc] of Object.entries(data.spartan_checks)) {
      if (!sc.spartan_available) continue;
      lines.push(
        `${key}: spartan_exits=${sc.spartan_exit_count}, bau_attrition=${sc.bau_attrition_count}, new_hires=${sc.new_hire_count}, ` +
          `offenders_in_hrms=${sc.offenders_hrms_count}, overdue_spartan=${sc.overdue_spartan_count}`
      );
      if (sc.payroll?.payroll_available) {
        lines.push(
          `  Payroll (${sc.payroll.payroll_cycle_start}→${sc.payroll.payroll_cycle_end}): count=${sc.payroll.payroll_count}, flagged=${sc.payroll.flagged_count}`
        );
      }
    }
  }

  // ── Span summary ──────────────────────────────────────────────────────────
  if (data.span) {
    lines.push("\n## Span / Role Movement");
    if (data.span.cluster_status) lines.push(`Cluster status: ${data.span.cluster_status}`);
    if (data.span.unknown_grades?.length > 0) {
      lines.push(`Unknown grades needing classification: ${data.span.unknown_grades.join(", ")}`);
    }
    if (data.span.cluster_summary?.length > 0) {
      lines.push("Cluster summary rows:");
      data.span.cluster_summary.slice(0, 10).forEach((row) => {
        const rowStr = Object.entries(row)
          .filter(([, v]) => v != null)
          .map(([k, v]) => `${k}=${v}`)
          .join(", ");
        if (rowStr) lines.push("  " + rowStr);
      });
    }
  }

  // ── Validation warnings ───────────────────────────────────────────────────
  if (data.validation_warnings?.length > 0) {
    lines.push("\n## Validation Warnings");
    data.validation_warnings.forEach((w) => lines.push(`- [${w.file}] ${w.message}`));
  }

  return lines.join("\n");
}
