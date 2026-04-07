"use client";

import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { TrendData } from "@/lib/types";

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

interface StatCardsProps {
  trend: TrendData;
}

export function StatCards({ trend }: StatCardsProps) {
  const len = trend.total.length;
  if (len === 0) return null;

  const latest = len - 1;
  const prev = len >= 2 ? len - 2 : null;

  function pctChange(arr: number[]): number | null {
    if (prev === null || arr[prev] === 0) return null;
    return ((arr[latest] - arr[prev]) / arr[prev]) * 100;
  }

  const cards = [
    { label: "Total Headcount", value: trend.total[latest], change: pctChange(trend.total), colorClass: "bg-stat-purple" },
    { label: "Delivery", value: trend.delivery[latest], change: pctChange(trend.delivery), colorClass: "bg-stat-blue" },
    { label: "Support Functions", value: trend.support[latest], change: pctChange(trend.support), colorClass: "bg-stat-orange" },
    { label: "CXO", value: trend.cxo[latest], change: pctChange(trend.cxo), colorClass: "bg-stat-green" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <StatCard key={card.label} {...card} />
      ))}
    </div>
  );
}
