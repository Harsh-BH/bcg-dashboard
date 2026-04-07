"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useDashboardStore } from "@/store/dashboardStore";
import { DrillDownTable } from "@/components/tables/DrillDownTable";
import { fetchDrill } from "@/lib/api";
import type { PersonRow } from "@/lib/types";
import { AnomalyAlertList } from "@/components/ai/AnomalyAlertList";

export function HrmsWalk() {
  const { data, reconBase, reconEnd, setRecon } = useDashboardStore();
  const [drillPeople, setDrillPeople] = useState<PersonRow[] | null>(null);
  const [drillTitle, setDrillTitle] = useState("");
  const [drillLoading, setDrillLoading] = useState(false);

  if (!data) return null;

  const { snapshots, reconciliation_tables, session_id } = data;
  const labels = snapshots.map((s) => s.label);
  const safeBase = reconBase ?? labels[0] ?? "";
  const safeEnd = reconEnd ?? labels[labels.length - 1] ?? "";
  const pairKey = `${safeBase} → ${safeEnd}`;
  const recData = reconciliation_tables[pairKey];

  const clickableKeys = recData
    ? [
        recData.base_label,
        `-Spartan exits till ${recData.end_label}`,
        "-BAU attrition",
        "-New hires",
        `${recData.end_label} (End-point)`,
      ]
    : [];

  function resolveSnapshotLabel(colKey: string): string {
    if (!recData) return colKey;
    const reconKey = `${recData.base_label}→${recData.end_label}`;
    if (colKey === recData.base_label) return recData.base_label;
    if (colKey.startsWith("-Spartan exits")) return `__recon__${reconKey}__spartan_exits`;
    if (colKey === "-BAU attrition") return `__recon__${reconKey}__bau_attrition`;
    if (colKey === "-New hires") return `__recon__${reconKey}__new_hires`;
    return recData.end_label;
  }

  return (
    <div className="space-y-6">
      <AnomalyAlertList tab="hrms-walk" />
      <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-border">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold text-foreground">
            Detailed reconciliation
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Click any headcount number in Baseline, Spartan exits, BAU attrition, New hires, or End-point
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Base</span>
              <Select value={safeBase} onValueChange={(v) => { if (v) { setRecon(v, safeEnd); setDrillPeople(null); } }}>
                <SelectTrigger className="w-48 h-9 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {labels.map((l) => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Compare</span>
              <Select value={safeEnd} onValueChange={(v) => { if (v) { setRecon(safeBase, v); setDrillPeople(null); } }}>
                <SelectTrigger className="w-48 h-9 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {labels.map((l) => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          {safeBase === safeEnd ? (
            <p className="text-sm text-amber-600">Comparison month must be later than base month.</p>
          ) : recData ? (
            <DrillDownTable
              rows={recData.rows}
              clickableKeys={clickableKeys}
              onCellClick={async (row, colKey) => {
                const label = String(row["Headcount"] ?? "").trim();
                setDrillTitle(`${label} · ${colKey}`);
                setDrillLoading(true);
                setDrillPeople(null);
                try {
                  const snapshotLabel = resolveSnapshotLabel(colKey);
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
              downloadFilename={`reconciliation_${pairKey.replace(" → ", "_to_")}.xlsx`}
            />
          ) : (
            <p className="text-sm text-muted-foreground">No data for this pair.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
