"use client";

import { AlertTriangle, AlertCircle, Info, FileText, Brain, Clock } from "lucide-react";
import { useDashboardStore } from "@/store/dashboardStore";
import type { Anomaly } from "@/lib/types";

const severityConfig = {
  high: { icon: AlertTriangle, color: "text-red-500", bg: "bg-red-50 dark:bg-red-950/30" },
  medium: { icon: AlertCircle, color: "text-amber-500", bg: "bg-amber-50 dark:bg-amber-950/30" },
  low: { icon: Info, color: "text-blue-500", bg: "bg-blue-50 dark:bg-blue-950/30" },
};

const tabLabels: Record<string, string> = {
  overall: "Overall",
  "hrms-walk": "HRMS Walk",
  span: "Span",
  spartan: "Spartan",
};

function AnomalyItem({ anomaly }: { anomaly: Anomaly }) {
  const config = severityConfig[anomaly.severity];
  const Icon = config.icon;

  return (
    <div className="flex items-start gap-3 py-2">
      <div className={`w-8 h-8 rounded-full ${config.bg} flex items-center justify-center shrink-0`}>
        <Icon size={14} className={config.color} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-foreground leading-tight">{anomaly.title}</p>
        <p className="text-xs text-muted-foreground mt-0.5">{tabLabels[anomaly.tab]} tab</p>
      </div>
    </div>
  );
}

export function ActivityPanel() {
  const { anomalies, data } = useDashboardStore();

  if (!data) return null;

  return (
    <aside className="w-[260px] shrink-0 border-l border-border bg-card h-screen sticky top-0 overflow-y-auto hidden xl:block">
      <div className="p-5 space-y-6">
        {/* Anomaly Alerts */}
        {anomalies.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-3">Alerts</h3>
            <div className="space-y-1 divide-y divide-border">
              {anomalies.slice(0, 5).map((a, i) => (
                <AnomalyItem key={i} anomaly={a} />
              ))}
            </div>
            {anomalies.length > 5 && (
              <p className="text-xs text-muted-foreground mt-2">
                +{anomalies.length - 5} more alerts
              </p>
            )}
          </div>
        )}

        {/* Snapshots loaded */}
        <div>
          <h3 className="text-sm font-semibold text-foreground mb-3">Loaded Snapshots</h3>
          <div className="space-y-2">
            {data.snapshots.map((s, i) => (
              <div key={i} className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                  <FileText size={14} className="text-muted-foreground" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-foreground truncate">{s.label}</p>
                  <p className="text-xs text-muted-foreground">{s.file_name}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Quick Stats */}
        <div>
          <h3 className="text-sm font-semibold text-foreground mb-3">Quick Stats</h3>
          <div className="space-y-2.5">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                <Brain size={14} className="text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{anomalies.length} anomalies</p>
                <p className="text-xs text-muted-foreground">detected by AI</p>
              </div>
            </div>
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                <Clock size={14} className="text-muted-foreground" />
              </div>
              <div>
                <p className="text-sm font-medium text-foreground">{data.snapshots.length} months</p>
                <p className="text-xs text-muted-foreground">of data loaded</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}
