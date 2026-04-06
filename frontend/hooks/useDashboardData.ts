"use client";

import { useMutation } from "@tanstack/react-query";
import { processFiles, type ProcessPayload } from "@/lib/api";
import { useDashboardStore } from "@/store/dashboardStore";
import { buildDashboardContext } from "@/lib/ai-context";
import type { Anomaly, ProcessResponse } from "@/lib/types";

async function runAnomalyDetection(data: ProcessResponse) {
  const store = useDashboardStore.getState();
  store.setAnomalyLoading(true);
  store.setAnomalies([]);
  try {
    const ctx = buildDashboardContext(data);
    const res = await fetch("/api/ai/anomalies", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ dashboardContext: ctx }),
    });
    const json = await res.json() as { anomalies?: Anomaly[] };
    store.setAnomalies(json.anomalies ?? []);
  } catch {
    // Anomaly detection is non-critical; silently fail
  } finally {
    store.setAnomalyLoading(false);
  }
}

export function useDashboardData() {
  const setData = useDashboardStore((s) => s.setData);
  const setPreview = useDashboardStore((s) => s.setPreview);
  const setRecon = useDashboardStore((s) => s.setRecon);
  const setSpanMonths = useDashboardStore((s) => s.setSpanMonths);
  const setIsLoading = useDashboardStore((s) => s.setIsLoading);

  return useMutation({
    mutationFn: (payload: ProcessPayload) => processFiles(payload),
    onMutate: () => setIsLoading(true),
    onSettled: () => setIsLoading(false),
    onSuccess: (data) => {
      setData(data);
      const labels = data.snapshots.map((s) => s.label);
      if (labels.length >= 2) {
        setPreview(labels[0], labels[labels.length - 1]);
        setRecon(labels[0], labels[labels.length - 1]);
      }
      setSpanMonths(labels);
      // Fire-and-forget anomaly detection
      runAnomalyDetection(data);
    },
  });
}
