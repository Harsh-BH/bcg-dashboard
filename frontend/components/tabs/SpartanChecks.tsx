"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Download, AlertTriangle, CheckCircle2, Info } from "lucide-react";
import { useDashboardStore } from "@/store/dashboardStore";
import { downloadExcel } from "@/lib/utils";
import type { SpartanChecksData, PayrollChecksData } from "@/lib/types";
import { AnomalyAlertList } from "@/components/ai/AnomalyAlertList";

function MetricCard({
  label,
  value,
  sub,
}: {
  label: string;
  value: number | string;
  sub?: string;
}) {
  return (
    <div className="rounded-xl border border-border bg-card px-4 py-3 shadow-sm flex flex-col gap-0.5">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="text-2xl font-bold tabular-nums text-foreground">
        {typeof value === "number" ? value.toLocaleString() : value}
      </span>
      {sub && <span className="text-xs text-muted-foreground">{sub}</span>}
    </div>
  );
}

function SimpleTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) return <p className="text-sm text-muted-foreground">No data</p>;
  const keys = Object.keys(rows[0]);
  return (
    <div className="overflow-x-auto rounded-xl border border-border">
      <table className="w-full text-xs">
        <thead className="bg-[hsl(var(--table-header))] text-white">
          <tr>
            {keys.map((k, i) => (
              <th key={k} className={`px-3 py-2 font-semibold ${i === 0 ? "text-left" : "text-right"}`}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-border hover:bg-muted/50">
              {keys.map((k, ci) => {
                const v = row[k];
                const display = typeof v === "number" ? v.toLocaleString() : String(v ?? "—");
                return (
                  <td key={k} className={`px-3 py-1.5 text-foreground ${ci === 0 ? "text-left" : "text-right tabular-nums"}`}>
                    {display}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function PayrollSection({ payroll }: { payroll: PayrollChecksData }) {
  if (!payroll.payroll_available) {
    return (
      <Alert className="border-border bg-muted/50">
        <Info className="h-4 w-4 text-muted-foreground" />
        <AlertDescription className="text-muted-foreground text-xs">
          {payroll.spartan_required
            ? "Upload a Spartan file to enable payroll cross-check."
            : "No payroll file uploaded. Upload a payroll file to run the Spartan vs Payroll cross-check."}
        </AlertDescription>
      </Alert>
    );
  }

  const flagged = payroll.flagged_count ?? 0;

  return (
    <div className="space-y-4">
      {payroll.payroll_cycle_start && (
        <p className="text-xs text-muted-foreground">
          Payroll cycle: {payroll.payroll_cycle_start} → {payroll.payroll_cycle_end}
        </p>
      )}

      <div className="grid grid-cols-2 gap-3">
        <MetricCard label="Employees in payroll file" value={payroll.payroll_count ?? 0} />
        <MetricCard
          label="Flagged (in payroll AND LWD ≤ cycle end)"
          value={flagged}
        />
      </div>

      {flagged === 0 ? (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700 text-xs font-medium">
            No Spartan exits found in payroll with LWD within the payroll cycle.
          </AlertDescription>
        </Alert>
      ) : (
        <Alert className="border-red-200 bg-red-50">
          <AlertTriangle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-700 text-xs font-medium">
            {flagged.toLocaleString()} Spartan exit{flagged !== 1 ? "s are" : " is"} still present in payroll with LWD ≤ cycle end.
          </AlertDescription>
        </Alert>
      )}

      {(payroll.flagged?.length ?? 0) > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-sm font-semibold text-foreground">
              Flagged employees ({flagged.toLocaleString()})
            </p>
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1"
              onClick={() =>
                downloadExcel(
                  payroll.flagged as Record<string, unknown>[],
                  "payroll_spartan_flagged.xlsx"
                )
              }
            >
              <Download size={12} /> Excel
            </Button>
          </div>
          <SimpleTable rows={payroll.flagged as Record<string, unknown>[]} />
        </div>
      )}
    </div>
  );
}

function SpartanSection({ checks, snapshotLabel }: { checks: SpartanChecksData; snapshotLabel: string }) {
  if (!checks.spartan_available) {
    return (
      <Alert className="border-border bg-muted/50">
        <Info className="h-4 w-4 text-muted-foreground" />
        <AlertDescription className="text-muted-foreground text-xs">
          No Spartan file uploaded. Upload a Spartan file to see exit and attrition checks.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {checks.spartan_report && (
        <p className="text-xs text-muted-foreground">
          Detected sheet: <span className="font-mono">{checks.spartan_report.sheet_used}</span>
          {" "}· header row {checks.spartan_report.header_row}
        </p>
      )}

      <div className="grid grid-cols-3 gap-3">
        <MetricCard label="Spartan exits" value={checks.spartan_exit_count} />
        <MetricCard label="BAU attrition" value={checks.bau_attrition_count} />
        <MetricCard label="New hires" value={checks.new_hire_count} />
      </div>

      {checks.offenders_hrms_count > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-foreground">
                In HRMS but should have exited
              </p>
              <Badge variant="destructive" className="text-xs">{checks.offenders_hrms_count}</Badge>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1"
              onClick={() =>
                downloadExcel(
                  checks.offenders_hrms as Record<string, unknown>[],
                  `hrms_overdue_exits_${snapshotLabel}.xlsx`
                )
              }
            >
              <Download size={12} /> Excel
            </Button>
          </div>
          <Alert className="border-red-200 bg-red-50">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-700 text-xs">
              These employees appear active in HRMS ({snapshotLabel}) but their Spartan exit date has passed.
            </AlertDescription>
          </Alert>
          <SimpleTable rows={checks.offenders_hrms as Record<string, unknown>[]} />
        </div>
      )}

      {checks.offenders_hrms_count === 0 && (
        <Alert className="border-green-200 bg-green-50">
          <CheckCircle2 className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-700 text-xs font-medium">
            No overdue exits found in HRMS — all Spartan exits have been processed.
          </AlertDescription>
        </Alert>
      )}

      {checks.overdue_spartan_count > 0 && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-foreground">
                Overdue in Spartan (not yet exited)
              </p>
              <Badge variant="outline" className="border-amber-400 text-amber-700 text-xs">
                {checks.overdue_spartan_count}
              </Badge>
            </div>
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1"
              onClick={() =>
                downloadExcel(
                  checks.overdue_spartan as Record<string, unknown>[],
                  `spartan_overdue_${snapshotLabel}.xlsx`
                )
              }
            >
              <Download size={12} /> Excel
            </Button>
          </div>
          <SimpleTable rows={checks.overdue_spartan as Record<string, unknown>[]} />
        </div>
      )}
    </div>
  );
}

export function SpartanChecks() {
  const { data } = useDashboardStore();

  if (!data) return null;

  const { spartan_checks, snapshots } = data;
  const entries = Object.entries(spartan_checks);

  if (entries.length === 0) {
    return (
      <Alert className="border-border bg-muted/50">
        <Info className="h-4 w-4 text-muted-foreground" />
        <AlertDescription className="text-muted-foreground text-sm">
          No Spartan or Payroll data available. Upload a Spartan or Payroll file and re-process.
        </AlertDescription>
      </Alert>
    );
  }

  // Use the last snapshot label for display context
  const lastLabel = snapshots[snapshots.length - 1]?.label ?? "";

  // All snapshots share the same payroll data — use the first entry
  const firstChecks = entries[0][1];

  return (
    <div className="space-y-6">
      <AnomalyAlertList tab="spartan" />
      {/* Spartan section — one per snapshot */}
      {entries.map(([snapshotLabel, checks]) => (
        <Card key={snapshotLabel} className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-border">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold text-foreground">
              Spartan cross-check — {snapshotLabel}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <SpartanSection checks={checks} snapshotLabel={snapshotLabel} />
          </CardContent>
        </Card>
      ))}

      {/* Payroll section — one card, taken from first entry */}
      <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold text-foreground">
            Payroll reconciliation
          </CardTitle>
          {firstChecks.payroll.payroll_available && (
            <p className="text-xs text-muted-foreground">
              Comparing HRMS ({lastLabel}) against uploaded payroll file
            </p>
          )}
        </CardHeader>
        <CardContent>
          <PayrollSection payroll={firstChecks.payroll} />
        </CardContent>
      </Card>
    </div>
  );
}
