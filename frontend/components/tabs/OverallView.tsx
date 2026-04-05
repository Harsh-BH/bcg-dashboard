"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { HeadcountTrendChart } from "@/components/charts/HeadcountTrendChart";
import { DrillDownTable } from "@/components/tables/DrillDownTable";
import { useDashboardStore } from "@/store/dashboardStore";
import { fmtPct, fmtNum, downloadExcel } from "@/lib/utils";
import { fetchDrill } from "@/lib/api";
import type { HierRow, PersonRow } from "@/lib/types";
import { AnomalyAlertList } from "@/components/ai/AnomalyAlertList";

const METRICS = [
  { value: "total", label: "Total headcount" },
  { value: "delivery", label: "Delivery" },
  { value: "support", label: "Support Functions" },
  { value: "cxo", label: "CXO" },
] as const;

export function OverallView() {
  const { data, previewStart, previewEnd, setPreview } = useDashboardStore();
  const [metric, setMetric] = useState<"total" | "delivery" | "support" | "cxo">("total");
  const [drillPeople, setDrillPeople] = useState<PersonRow[] | null>(null);
  const [drillTitle, setDrillTitle] = useState("");
  const [drillLoading, setDrillLoading] = useState(false);

  if (!data) return null;

  const { trend, overview_table, pair_tables, snapshots, session_id } = data;
  const labels = snapshots.map((s) => s.label);

  const safeStart = previewStart ?? labels[0] ?? "";
  const safeEnd = previewEnd ?? labels[labels.length - 1] ?? "";
  const pairKey = `${safeStart} → ${safeEnd}`;
  const pairData = pair_tables[pairKey];

  const hierRows: HierRow[] = pairData?.hier_rows ?? [];

  const startDate = safeStart !== safeEnd ? safeStart : undefined;

  return (
    <div className="space-y-6">
      <AnomalyAlertList tab="overall" />
      {/* Trend chart */}
      <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-slate-100">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between flex-wrap gap-3">
            <CardTitle className="text-base font-semibold text-slate-800">
              Headcount trend
            </CardTitle>
            <Select value={metric} onValueChange={(v) => setMetric(v as typeof metric)}>
              <SelectTrigger className="w-44 h-9 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {METRICS.map((m) => (
                  <SelectItem key={m.value} value={m.value}>
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          <HeadcountTrendChart trend={trend} metric={metric} />
        </CardContent>
      </Card>

      {/* MoM overview table */}
      <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-slate-100">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-base font-semibold text-slate-800">
              Month-on-month overview
            </CardTitle>
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1"
              onClick={() => downloadExcel(overview_table as unknown as Record<string, unknown>[], "mom_overview.xlsx")}
            >
              <Download size={12} /> Excel
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto rounded-xl border border-slate-200">
            <table className="w-full text-sm">
              <thead className="bg-table-header text-white">
                <tr>
                  {["Start", "End", "Start HC", "End HC", "Abs Δ", "% Δ", "% Δ Delivery", "% Δ CXO", "% Δ Support"].map(
                    (h, i) => (
                      <th
                        key={h}
                        className={`px-3 py-2.5 font-semibold text-xs ${i > 1 ? "text-right" : "text-left"}`}
                      >
                        {h}
                      </th>
                    )
                  )}
                </tr>
              </thead>
              <tbody>
                {overview_table.map((row, ri) => (
                  <tr key={ri} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="px-3 py-2 text-slate-700 whitespace-nowrap">{row.start_month}</td>
                    <td className="px-3 py-2 text-slate-700 whitespace-nowrap">{row.end_month}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmtNum(row.start_hc)}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmtNum(row.end_hc)}</td>
                    <td className={`px-3 py-2 text-right tabular-nums font-medium ${row.abs_change > 0 ? "text-red-600" : row.abs_change < 0 ? "text-green-600" : ""}`}>
                      {row.abs_change > 0 ? "+" : ""}{fmtNum(row.abs_change)}
                    </td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmtPct(row.pct_change)}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmtPct(row.pct_change_delivery)}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmtPct(row.pct_change_cxo)}</td>
                    <td className="px-3 py-2 text-right tabular-nums">{fmtPct(row.pct_change_support)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Pair preview with drill-down */}
      <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-slate-100">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold text-slate-800">
            Detailed pair preview
          </CardTitle>
          <p className="text-xs text-slate-500">Click a headcount number to see the employee list</p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 whitespace-nowrap">Start</span>
              <Select value={safeStart} onValueChange={(v) => { if (v) { setPreview(v, safeEnd); setDrillPeople(null); } }}>
                <SelectTrigger className="w-48 h-9 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {labels.map((l) => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500 whitespace-nowrap">End</span>
              <Select value={safeEnd} onValueChange={(v) => { if (v) { setPreview(safeStart, v); setDrillPeople(null); } }}>
                <SelectTrigger className="w-48 h-9 text-xs">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {labels.map((l) => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          {safeStart === safeEnd ? (
            <p className="text-sm text-amber-600">End month must be later than start month.</p>
          ) : pairData ? (
            <DrillDownTable
              rows={hierRows.map((r) => ({ label: r.label, _rowtype: r.rowtype, ...r.values }))}
              clickableKeys={[pairData.start_label, pairData.end_label]}
              onCellClick={async (row, colKey) => {
                const label = String(row["label"] ?? "").trim();
                setDrillTitle(`${label} · ${colKey}`);
                setDrillLoading(true);
                setDrillPeople(null);
                try {
                  const snapshotLabel = colKey === pairData.start_label
                    ? pairData.start_label
                    : pairData.end_label;
                  const res = await fetchDrill(session_id, snapshotLabel, label);
                  setDrillPeople(res.people);
                } catch {
                  setDrillPeople([]);
                } finally {
                  setDrillLoading(false);
                }
              }}
              drillPeople={drillPeople ?? undefined}
              drillTitle={drillTitle}
              drillLoading={drillLoading}
              downloadFilename={`headcount_${pairKey.replace(" → ", "_to_")}.xlsx`}
            />
          ) : (
            <p className="text-sm text-slate-500">No data for this pair.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
