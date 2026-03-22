"use client";

import { cn } from "@/lib/utils";
import type { HierRow } from "@/lib/types";

interface HierarchyTableProps {
  rows: HierRow[];
  columns: { key: string; label: string }[];
  onCellClick?: (row: HierRow, colKey: string) => void;
  clickableKeys?: Set<string>;
}

const rowtypeStyle: Record<string, string> = {
  grand:  "bg-[hsl(var(--row-grand))] font-bold text-slate-900",
  header: "bg-[hsl(var(--row-header))] font-semibold text-slate-800",
  child:  "bg-white text-slate-700 hover:bg-slate-50/80 transition-colors duration-100",
};

export function HierarchyTable({
  rows,
  columns,
  onCellClick,
  clickableKeys,
}: HierarchyTableProps) {
  return (
    <div className="rounded-xl overflow-hidden shadow-sm border border-slate-200">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-table-header">
            {columns.map((col, i) => (
              <th
                key={col.key}
                className={cn(
                  "px-3 py-2.5 text-white font-semibold text-xs",
                  i === 0 ? "text-left" : "text-right"
                )}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => (
            <tr
              key={ri}
              className={cn(
                rowtypeStyle[row.rowtype] ?? "bg-white hover:bg-slate-50/80 transition-colors duration-100",
                "border-b border-slate-100 last:border-0"
              )}
            >
              {columns.map((col, ci) => {
                const raw = ci === 0 ? row.label : row.values[col.key];
                const isClickable =
                  ci > 0 && clickableKeys?.has(col.key) && typeof raw === "number";

                let textClass = "";
                if (col.key.includes("change") || col.key.includes("Abs")) {
                  const num = typeof raw === "number" ? raw : parseFloat(String(raw));
                  if (!isNaN(num) && row.rowtype === "child") {
                    textClass = num > 0 ? "text-red-600" : num < 0 ? "text-emerald-600" : "";
                  }
                }

                const display =
                  typeof raw === "number" && col.key.includes("%")
                    ? `${(raw * 100).toFixed(1)}%`
                    : typeof raw === "number"
                    ? raw.toLocaleString()
                    : (raw ?? "—");

                return (
                  <td
                    key={col.key}
                    onClick={isClickable ? () => onCellClick?.(row, col.key) : undefined}
                    className={cn(
                      "px-3 py-2",
                      ci === 0 ? "text-left" : "text-right tabular-nums",
                      textClass,
                      isClickable &&
                        "cursor-pointer hover:bg-blue-50 hover:text-blue-700 rounded transition-colors duration-100"
                    )}
                  >
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
