"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LabelList,
} from "recharts";
import type { TrendData } from "@/lib/types";

interface Props {
  trend: TrendData;
  metric: keyof Omit<TrendData, "labels">;
}

const metricColors: Record<string, string> = {
  total:    "#3b82f6",
  delivery: "#10b981",
  support:  "#f59e0b",
  cxo:      "#8b5cf6",
};

const metricLabels: Record<string, string> = {
  total:    "Total headcount",
  delivery: "Delivery",
  support:  "Support Functions",
  cxo:      "CXO",
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function CustomTooltip({ active, payload, label, color, metricKey }: any) {
  if (!active || !payload?.length) return null;
  const value = payload[0]?.value as number;
  return (
    <div className="rounded-xl border border-border bg-card shadow-xl px-4 py-3 min-w-[150px]">
      <p className="text-muted-foreground text-xs font-medium mb-2">{label}</p>
      <div className="flex items-center gap-2.5">
        <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ background: color }} />
        <div>
          <p className="font-bold text-foreground text-lg tabular-nums leading-none">
            {value?.toLocaleString()}
          </p>
          <p className="text-muted-foreground text-xs mt-0.5">{metricLabels[metricKey] ?? metricKey}</p>
        </div>
      </div>
    </div>
  );
}

export function HeadcountTrendChart({ trend, metric }: Props) {
  const color = metricColors[metric] ?? "#3b82f6";
  const gradientId = `grad-${metric}`;

  const data = trend.labels.map((label, i) => ({
    month: label,
    value: trend[metric][i],
  }));

  return (
    <ResponsiveContainer width="100%" height={320}>
      <AreaChart data={data} margin={{ top: 28, right: 32, bottom: 8, left: 0 }}>
        {/* Gradient fill definition */}
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%"   stopColor={color} stopOpacity={0.18} />
            <stop offset="100%" stopColor={color} stopOpacity={0}    />
          </linearGradient>
        </defs>

        {/* Clean horizontal-only grid */}
        <CartesianGrid stroke="#f1f5f9" vertical={false} />

        <XAxis
          dataKey="month"
          tick={{ fontSize: 12, fill: "#64748b", fontWeight: 500 }}
          tickLine={false}
          axisLine={false}
          dy={6}
        />
        <YAxis
          width={54}
          tick={{ fontSize: 12, fill: "#64748b", fontWeight: 500 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => v.toLocaleString()}
        />

        <Tooltip
          content={<CustomTooltip color={color} metricKey={metric} />}
          cursor={{ stroke: color, strokeWidth: 1.5, strokeDasharray: "4 3", opacity: 0.45 }}
        />

        <Area
          type="monotone"
          dataKey="value"
          stroke={color}
          strokeWidth={2.5}
          fill={`url(#${gradientId})`}
          dot={{ r: 4, fill: "#fff", stroke: color, strokeWidth: 2.5 }}
          activeDot={{ r: 7, fill: color, stroke: "#fff", strokeWidth: 2.5 }}
        >
          <LabelList
            dataKey="value"
            position="top"
            style={{ fontSize: 12, fill: "#334155", fontWeight: 700 }}
            formatter={(v: unknown) => (v as number).toLocaleString()}
          />
        </Area>
      </AreaChart>
    </ResponsiveContainer>
  );
}
