"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { ChevronDown, Download } from "lucide-react";

const triggerCls = "flex items-center gap-1 text-xs text-slate-600 bg-transparent border-0 cursor-pointer hover:text-slate-800 py-1 px-2 rounded-md hover:bg-slate-100 transition-colors";
import { useDashboardStore } from "@/store/dashboardStore";
import { downloadMultiSheetExcel, downloadExcel } from "@/lib/utils";
import { AnomalyAlertList } from "@/components/ai/AnomalyAlertList";

function SimpleTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) return <p className="text-sm text-slate-500">No data</p>;
  const keys = Object.keys(rows[0]);
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200">
      <table className="w-full text-xs">
        <thead className="bg-slate-800 text-white">
          <tr>
            {keys.map((k, i) => (
              <th key={k} className={`px-3 py-2 font-semibold ${i === 0 ? "text-left" : "text-right"}`}>{k}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr key={ri} className="border-b border-slate-100 hover:bg-slate-50">
              {keys.map((k, ci) => {
                const v = row[k];
                const display = typeof v === "number" ? v.toLocaleString() : String(v ?? "—");
                return (
                  <td key={k} className={`px-3 py-1.5 text-slate-700 ${ci === 0 ? "text-left" : "text-right tabular-nums"}`}>
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

export function SpanMovement() {
  const { data } = useDashboardStore();

  if (!data) return null;
  const { span } = data;

  return (
    <div className="space-y-6">
      <AnomalyAlertList tab="span" />
      {/* Unknown grades notice */}
      {span.unknown_grades.length > 0 && (
        <Card className="rounded-2xl border-amber-200 bg-amber-50/50">
          <CardContent className="pt-4">
            <p className="text-sm font-medium text-amber-800 mb-1">Unknown grades detected</p>
            <div className="flex flex-wrap gap-1.5">
              {span.unknown_grades.map((g) => (
                <Badge key={g} variant="outline" className="border-amber-400 text-amber-700">{g}</Badge>
              ))}
            </div>
            <p className="text-xs text-amber-600 mt-2">
              These grades are outside known rules and default to M1+. Re-submit with grade overrides when supported.
            </p>
          </CardContent>
        </Card>
      )}

      {/* MoM cluster trend */}
      {span.trend_long.length > 0 && (
        <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-slate-100">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold text-slate-800">
                Span by cluster × month
              </CardTitle>
              <Button size="sm" variant="outline" className="h-7 text-xs gap-1"
                onClick={() => downloadExcel(span.trend_long as Record<string, unknown>[], "span_trend.xlsx")}>
                <Download size={12} /> Excel
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <SimpleTable rows={span.trend_long as Record<string, unknown>[]} />
          </CardContent>
        </Card>
      )}

      {/* Service line row counts */}
      {span.service_line_counts.length > 0 && (
        <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-slate-100">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base font-semibold text-slate-800">
                Service line × month (row counts)
              </CardTitle>
              <Button size="sm" variant="outline" className="h-7 text-xs gap-1"
                onClick={() =>
                  downloadMultiSheetExcel(
                    [
                      { name: "Row counts", rows: span.service_line_counts as Record<string, unknown>[] },
                      { name: "Span IC÷TL", rows: span.service_line_span as Record<string, unknown>[] },
                      { name: "IC TL M1+ counts", rows: span.service_line_roles as Record<string, unknown>[] },
                    ],
                    "span_service_line.xlsx"
                  )
                }
              >
                <Download size={12} /> Excel (3 sheets)
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <SimpleTable rows={span.service_line_counts as Record<string, unknown>[]} />

            {span.service_line_span.length > 0 && (
              <>
                <p className="text-sm font-semibold text-slate-700 mt-4">Span (IC ÷ TL) by service line</p>
                <SimpleTable rows={span.service_line_span as Record<string, unknown>[]} />
              </>
            )}

            {span.service_line_roles.length > 0 && (
              <Collapsible>
                <CollapsibleTrigger className={triggerCls}>
                  IC / TL / M1+ counts by service line <ChevronDown size={12} />
                </CollapsibleTrigger>
                <CollapsibleContent className="mt-2">
                  <SimpleTable rows={span.service_line_roles as Record<string, unknown>[]} />
                </CollapsibleContent>
              </Collapsible>
            )}
          </CardContent>
        </Card>
      )}

      {/* Single snapshot detail */}
      <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-slate-100">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold text-slate-800">
            Single snapshot — {span.single_snapshot_label}
          </CardTitle>
          {span.cluster_status && (
            <p className="text-xs text-slate-500">{span.cluster_status}</p>
          )}
        </CardHeader>
        <CardContent className="space-y-4">
          {span.cluster_summary.length > 0 && (
            <>
              <p className="text-sm font-semibold text-slate-700">Span counts by cluster</p>
              <SimpleTable rows={span.cluster_summary as Record<string, unknown>[]} />
            </>
          )}

          {span.single_snapshot_roles.length > 0 && (
            <Collapsible>
              <CollapsibleTrigger className={triggerCls}>
                All classified rows (first 200) <ChevronDown size={12} />
              </CollapsibleTrigger>
              <CollapsibleContent className="mt-2">
                <SimpleTable rows={(span.single_snapshot_roles as Record<string, unknown>[]).slice(0, 200)} />
                {span.single_snapshot_roles.length > 200 && (
                  <p className="text-xs text-slate-400 mt-1">
                    Showing 200 of {span.single_snapshot_roles.length.toLocaleString()} rows. Download for full data.
                  </p>
                )}
              </CollapsibleContent>
            </Collapsible>
          )}

          {span.single_snapshot_roles.length > 0 && (
            <Button size="sm" variant="outline" className="h-7 text-xs gap-1"
              onClick={() => downloadExcel(span.single_snapshot_roles as Record<string, unknown>[], `span_${span.single_snapshot_label}.xlsx`)}>
              <Download size={12} /> Download Excel
            </Button>
          )}
        </CardContent>
      </Card>

      {/* TL designation phrases */}
      <Collapsible>
        <CollapsibleTrigger className={`${triggerCls} text-slate-500`}>
          TL designation phrases (A1/A2 mandatory TL) <ChevronDown size={12} />
        </CollapsibleTrigger>
        <CollapsibleContent>
          <Card className="mt-2 rounded-xl border-slate-100">
            <CardContent className="pt-4 text-xs text-slate-600">
              <p className="mb-2">If grade is A1.x or A2.x and designation matches any of these (spaces ignored):</p>
              <div className="flex flex-wrap gap-1.5">
                {["team lead","team leader","team manager","senior manager","senior manager quality","senior officer","lead","srtl","supervisor"].map((p) => (
                  <Badge key={p} variant="secondary" className="font-mono text-xs">{p}</Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}
