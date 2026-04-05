"use client";

import { useState } from "react";
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
} from "@tanstack/react-table";
import { ChevronDown, ChevronUp, ChevronsUpDown, Download } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn, downloadExcel } from "@/lib/utils";
import type { PersonRow } from "@/lib/types";

interface DrillDownTableProps {
  rows: Record<string, unknown>[];
  columnKeys?: string[];
  clickableKeys?: string[];
  onCellClick?: (row: Record<string, unknown>, colKey: string) => void;
  drillPeople?: PersonRow[];
  drillTitle?: string;
  drillLoading?: boolean;
  downloadFilename?: string;
  className?: string;
}

export function DrillDownTable({
  rows,
  columnKeys,
  clickableKeys,
  onCellClick,
  drillPeople,
  drillTitle,
  drillLoading,
  downloadFilename,
  className,
}: DrillDownTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);

  const keys = columnKeys ?? (rows[0] ? Object.keys(rows[0]).filter((k) => k !== "_rowtype") : []);

  const columns: ColumnDef<Record<string, unknown>>[] = keys.map((key, i) => ({
    accessorKey: key,
    header: ({ column }) => (
      <button
        className="flex items-center gap-1 hover:text-white/80 transition-colors"
        onClick={() => column.toggleSorting(column.getIsSorted() === "asc")}
      >
        {key}
        {column.getIsSorted() === "asc" ? (
          <ChevronUp size={12} />
        ) : column.getIsSorted() === "desc" ? (
          <ChevronDown size={12} />
        ) : (
          <ChevronsUpDown size={12} className="opacity-40" />
        )}
      </button>
    ),
    cell: ({ getValue, row }) => {
      const v = getValue();
      const isClickable = clickableKeys?.includes(key) && typeof v === "number";
      const display =
        typeof v === "number"
          ? key.toLowerCase().includes("pct") || key.includes("%")
            ? `${(v * 100).toFixed(1)}%`
            : v.toLocaleString()
          : (v as string) ?? "—";

      let textClass = "";
      const rowtype = row.original["_rowtype"] as string | undefined;
      if ((key.includes("Abs") || key.includes("change")) && rowtype === "child") {
        const num = typeof v === "number" ? v : parseFloat(String(v));
        if (!isNaN(num)) textClass = num > 0 ? "text-red-600" : num < 0 ? "text-emerald-600" : "";
      }

      return (
        <span
          onClick={isClickable ? () => onCellClick?.(row.original, key) : undefined}
          className={cn(
            i === 0 ? "text-left" : "text-right block tabular-nums",
            textClass,
            isClickable &&
              "cursor-pointer text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-1.5 py-0.5 rounded-md transition-colors duration-100"
          )}
        >
          {display}
        </span>
      );
    },
  }));

  const table = useReactTable({
    data: rows,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const rowtypeStyle = (rt: string | undefined) => {
    if (rt === "grand")  return "bg-[hsl(var(--row-grand))] font-bold";
    if (rt === "header") return "bg-[hsl(var(--row-header))] font-semibold";
    return "bg-white hover:bg-slate-50/80 transition-colors duration-100";
  };

  const peopleKeys = drillPeople?.[0] ? Object.keys(drillPeople[0]).filter((k) => k !== "BUCKET") : [];

  return (
    <div className={cn("space-y-3", className)}>
      {/* Main table */}
      <div className="rounded-xl overflow-hidden shadow-sm border border-slate-200">
        {downloadFilename && rows.length > 0 && (
          <div className="flex justify-end px-3 py-2 bg-slate-50 border-b border-slate-200">
            <Button
              size="sm"
              variant="outline"
              className="h-7 text-xs gap-1"
              onClick={() => downloadExcel(rows, downloadFilename)}
            >
              <Download size={12} /> Excel
            </Button>
          </div>
        )}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              {table.getHeaderGroups().map((hg) => (
                <tr key={hg.id} className="bg-table-header">
                  {hg.headers.map((h, i) => (
                    <th
                      key={h.id}
                      className={cn(
                        "px-3 py-2.5 text-white font-semibold text-xs",
                        i === 0 ? "text-left" : "text-right"
                      )}
                    >
                      {flexRender(h.column.columnDef.header, h.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => {
                const rt = row.original["_rowtype"] as string | undefined;
                return (
                  <tr
                    key={row.id}
                    className={cn(rowtypeStyle(rt), "border-b border-slate-100 last:border-0")}
                  >
                    {row.getVisibleCells().map((cell, ci) => (
                      <td
                        key={cell.id}
                        className={cn("px-3 py-2", ci === 0 ? "text-left" : "text-right")}
                      >
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Drill-down loading */}
      {drillLoading && (
        <div className="rounded-xl border-l-4 border-blue-500 border border-slate-200 bg-blue-50/20 shadow-sm p-6 animate-in fade-in-0 duration-200">
          <div className="flex items-center gap-3">
            <div className="w-5 h-5 rounded-full border-2 border-transparent border-t-blue-500 animate-spin" />
            <span className="text-sm text-slate-600">{drillTitle ? `Loading ${drillTitle}…` : "Loading people…"}</span>
          </div>
        </div>
      )}

      {/* Drill-down panel */}
      {!drillLoading && drillPeople && drillPeople.length > 0 && (
        <div className="rounded-xl border-l-4 border-blue-500 border border-slate-200 bg-blue-50/20 shadow-sm overflow-hidden animate-in slide-in-from-top-2 fade-in-0 duration-200">
          <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white">
            <div className="flex items-center gap-2">
              <span className="font-semibold text-slate-800 text-sm">{drillTitle ?? "People"}</span>
              <Badge variant="secondary" className="text-xs">{drillPeople.length.toLocaleString()}</Badge>
            </div>
            {downloadFilename && (
              <Button
                size="sm"
                variant="outline"
                className="h-7 text-xs gap-1"
                onClick={() =>
                  downloadExcel(drillPeople as Record<string, unknown>[], `people_${downloadFilename}`)
                }
              >
                <Download size={12} /> Excel
              </Button>
            )}
          </div>
          <div className="overflow-x-auto max-h-80">
            <table className="w-full text-xs">
              <thead className="sticky top-0 bg-slate-100 shadow-[0_1px_0_0_#e2e8f0]">
                <tr>
                  {peopleKeys.map((k) => (
                    <th key={k} className="px-3 py-2 text-left text-slate-600 font-semibold whitespace-nowrap">
                      {k}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {drillPeople.map((row, ri) => (
                  <tr
                    key={ri}
                    className={cn(
                      "border-b border-slate-100 hover:bg-blue-50/40 transition-colors duration-100",
                      ri % 2 === 0 ? "bg-white" : "bg-slate-50/60"
                    )}
                  >
                    {peopleKeys.map((k) => (
                      <td key={k} className="px-3 py-1.5 text-slate-700 whitespace-nowrap">
                        {String(row[k] ?? "—")}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
