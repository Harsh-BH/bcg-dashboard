"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useDashboardStore } from "@/store/dashboardStore";
import { DrillDownTable } from "@/components/tables/DrillDownTable";
import type { PersonRow } from "@/lib/types";
import { AnomalyAlertList } from "@/components/ai/AnomalyAlertList";

const COL_LABELS: Record<string, string> = {
  Baseline: "Baseline",
  SpartanExits: "Spartan exits",
  BAUAttrition: "BAU attrition",
  NewHires: "New hires",
  Endpoint: "End-point",
};

export function HrmsWalk() {
  const { data, reconBase, reconEnd, setRecon } = useDashboardStore();
  const [drillPeople, setDrillPeople] = useState<PersonRow[] | null>(null);
  const [drillTitle, setDrillTitle] = useState("");

  if (!data) return null;

  const { snapshots, reconciliation_tables } = data;
  const labels = snapshots.map((s) => s.label);
  const safeBase = reconBase ?? labels[0] ?? "";
  const safeEnd = reconEnd ?? labels[labels.length - 1] ?? "";
  const pairKey = `${safeBase} → ${safeEnd}`;
  const recData = reconciliation_tables[pairKey];

  const peopleMapForCol: Record<string, Record<string, PersonRow[]>> = recData
    ? {
        [recData.base_label]: recData.baseline_people as Record<string, PersonRow[]>,
        [`-Spartan exits till ${recData.end_label}`]: recData.spartan_exit_people as Record<string, PersonRow[]>,
        ["-BAU attrition"]: recData.bau_attrition_people as Record<string, PersonRow[]>,
        ["-New hires"]: recData.new_hire_people as Record<string, PersonRow[]>,
        [`${recData.end_label} (End-point)`]: recData.end_people as Record<string, PersonRow[]>,
      }
    : {};

  const clickableKeys = recData ? Object.keys(peopleMapForCol) : [];

  return (
    <div className="space-y-6">
      <AnomalyAlertList tab="hrms-walk" />
      <Card className="rounded-2xl shadow-sm hover:shadow-md transition-shadow duration-200 border-slate-100">
        <CardHeader className="pb-2">
          <CardTitle className="text-base font-semibold text-slate-800">
            Detailed reconciliation
          </CardTitle>
          <p className="text-xs text-slate-500">
            Click any headcount number in Baseline, Spartan exits, BAU attrition, New hires, or End-point
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-3 flex-wrap">
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Base</span>
              <Select value={safeBase} onValueChange={(v) => { if (v) { setRecon(v, safeEnd); setDrillPeople(null); } }}>
                <SelectTrigger className="w-48 h-9 text-xs"><SelectValue /></SelectTrigger>
                <SelectContent>
                  {labels.map((l) => <SelectItem key={l} value={l} className="text-xs">{l}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-500">Compare</span>
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
              onCellClick={(row, colKey) => {
                const label = String(row["Headcount"] ?? "").trim();
                const people = peopleMapForCol[colKey]?.[label] ?? [];
                setDrillPeople(people as PersonRow[]);
                setDrillTitle(`${label} · ${colKey}`);
              }}
              drillPeople={drillPeople ?? undefined}
              drillTitle={drillTitle}
              downloadFilename={`reconciliation_${pairKey.replace(" → ", "_to_")}.xlsx`}
            />
          ) : (
            <p className="text-sm text-slate-500">No data for this pair.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
