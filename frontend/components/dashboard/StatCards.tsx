"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { ProcessResponse } from "@/lib/types";

interface StatCardProps {
  label: string;
  value: number;
  change: number | null;
  colorClass: string;
}

function StatCard({ label, value, change, colorClass }: StatCardProps) {
  const isPositive = change !== null && change > 0;
  const isNegative = change !== null && change < 0;

  return (
    <div className={`rounded-xl p-5 ${colorClass} border border-white/20`}>
      <p className="text-sm font-medium text-slate-600 dark:text-slate-300 mb-3">{label}</p>
      <div className="flex items-end justify-between">
        <p className="text-3xl font-bold text-slate-900 dark:text-white tabular-nums">
          {value.toLocaleString()}
        </p>
        {change !== null && (
          <div className={`flex items-center gap-1 text-xs font-semibold px-2 py-1 rounded-full ${
            isPositive
              ? "text-emerald-700 bg-emerald-100 dark:text-emerald-400 dark:bg-emerald-900/40"
              : isNegative
              ? "text-red-700 bg-red-100 dark:text-red-400 dark:bg-red-900/40"
              : "text-slate-600 bg-slate-100 dark:text-slate-400 dark:bg-slate-800"
          }`}>
            {isPositive ? (
              <TrendingUp size={12} />
            ) : isNegative ? (
              <TrendingDown size={12} />
            ) : (
              <Minus size={12} />
            )}
            {change > 0 ? "+" : ""}{change.toFixed(2)}%
          </div>
        )}
      </div>
    </div>
  );
}

/** Walk backwards to find the latest non-zero value in a trend array. */
function latestNonZero(arr: number[]): number {
  for (let i = arr.length - 1; i >= 0; i--) {
    if (arr[i] !== 0) return arr[i];
  }
  return arr[arr.length - 1] ?? 0;
}

interface StatCardsProps {
  data: ProcessResponse;
}

export function StatCards({ data }: StatCardsProps) {
  const { trend, overview_table } = data;
  const len = trend.total.length;
  if (len === 0) return null;

  // Use the last overview row for total headcount and percentage changes
  const lastOverview = overview_table.length > 0
    ? overview_table[overview_table.length - 1]
    : null;

  // overview_table pct values are already percentages (e.g. -100.0), NOT decimals
  const totalPctChange = lastOverview?.pct_change ?? null;
  const deliveryPctChange = lastOverview?.pct_change_delivery ?? null;
  const supportPctChange = lastOverview?.pct_change_support ?? null;
  const cxoPctChange = lastOverview?.pct_change_cxo ?? null;

  const cards = [
    { label: "Total Headcount", value: latestNonZero(trend.total), change: totalPctChange, colorClass: "bg-stat-purple" },
    { label: "Delivery", value: latestNonZero(trend.delivery), change: deliveryPctChange, colorClass: "bg-stat-blue" },
    { label: "Support Functions", value: latestNonZero(trend.support), change: supportPctChange, colorClass: "bg-stat-orange" },
    { label: "CXO", value: latestNonZero(trend.cxo), change: cxoPctChange, colorClass: "bg-stat-green" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} />
      ))}
    </div>
  );
}
