"use client";

import { useState } from "react";
import { useDashboardStore } from "@/store/dashboardStore";
import type { AnomalyTab } from "@/lib/types";
import { AlertTriangle, ChevronDown, ChevronUp, Loader2 } from "lucide-react";

interface Props {
  tab: AnomalyTab;
}

const severityConfig = {
  high:   { bg: "bg-red-50 border-red-200",   badge: "bg-red-100 text-red-700",   icon: "text-red-500" },
  medium: { bg: "bg-amber-50 border-amber-200", badge: "bg-amber-100 text-amber-700", icon: "text-amber-500" },
  low:    { bg: "bg-blue-50 border-blue-200",  badge: "bg-blue-100 text-blue-700", icon: "text-blue-500" },
};

export function AnomalyAlertList({ tab }: Props) {
  const allAnomalies = useDashboardStore((s) => s.anomalies);
  const anomalies = allAnomalies.filter((a) => a.tab === tab);
  const anomalyLoading = useDashboardStore((s) => s.anomalyLoading);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [collapsed, setCollapsed] = useState(false);

  if (anomalyLoading) {
    return (
      <div className="flex items-center gap-2 text-muted-foreground text-xs py-2 mb-4">
        <Loader2 size={12} className="animate-spin" />
        Scanning for anomalies…
      </div>
    );
  }

  if (!anomalies.length) return null;

  return (
    <div className="mb-5">
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center gap-2 mb-2 text-xs font-semibold text-foreground hover:text-foreground transition-colors"
      >
        <AlertTriangle size={13} className="text-amber-500" />
        {anomalies.length} Anomal{anomalies.length !== 1 ? "ies" : "y"} Detected
        {collapsed ? <ChevronDown size={13} /> : <ChevronUp size={13} />}
      </button>

      {!collapsed && (
        <div className="space-y-2 animate-in fade-in-0 slide-in-from-top-1 duration-200">
          {anomalies.map((a, idx) => {
            const id = `${tab}-${idx}`;
            const cfg = severityConfig[a.severity];
            return (
              <div key={id} className={`border rounded-xl px-3.5 py-3 ${cfg.bg}`}>
                <div className="flex items-start gap-2.5">
                  <AlertTriangle size={14} className={`shrink-0 mt-0.5 ${cfg.icon}`} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="text-sm font-semibold text-foreground">{a.title}</span>
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full uppercase ${cfg.badge}`}>
                        {a.severity}
                      </span>
                    </div>
                    <button
                      onClick={() => setExpanded(expanded === id ? null : id)}
                      className="text-xs text-muted-foreground hover:text-foreground mt-0.5 flex items-center gap-1 transition-colors"
                    >
                      {expanded === id ? "Hide details" : "Show details"}
                      {expanded === id ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                    </button>
                    {expanded === id && (
                      <p className="text-xs text-foreground mt-2 leading-relaxed animate-in fade-in-0 slide-in-from-top-1 duration-150">
                        {a.explanation}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
