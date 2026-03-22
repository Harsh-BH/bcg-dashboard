"use client";

import { useState, useCallback } from "react";
import { useDashboardStore } from "@/store/dashboardStore";
import { buildDashboardContext } from "@/lib/ai-context";
import { readStream } from "@/lib/claude-stream";

export type ReportProgress = "idle" | "commentary" | "anomalies" | "pdf" | "done";

export function useReportGeneration(chartRef: React.RefObject<HTMLElement | null>) {
  const data = useDashboardStore((s) => s.data);
  const commentary = useDashboardStore((s) => s.commentary);
  const setCommentary = useDashboardStore((s) => s.setCommentary);
  const anomalies = useDashboardStore((s) => s.anomalies);
  const setAnomalies = useDashboardStore((s) => s.setAnomalies);
  const [progress, setProgress] = useState<ReportProgress>("idle");

  const generate = useCallback(async () => {
    if (!data || progress !== "idle") return;

    const ctx = buildDashboardContext(data);

    // Step 1: Commentary
    let currentCommentary = commentary;
    if (!currentCommentary) {
      setProgress("commentary");
      let accumulated = "";
      try {
        for await (const chunk of readStream("/api/ai/commentary", { dashboardContext: ctx })) {
          accumulated += chunk;
        }
        setCommentary(accumulated);
        currentCommentary = accumulated;
      } catch { /* ignore, use empty */ }
    }

    // Step 2: Anomalies
    let currentAnomalies = anomalies;
    if (!currentAnomalies.length) {
      setProgress("anomalies");
      try {
        const res = await fetch("/api/ai/anomalies", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ dashboardContext: ctx }),
        });
        const json = await res.json();
        setAnomalies(json.anomalies ?? []);
        currentAnomalies = json.anomalies ?? [];
      } catch { /* ignore */ }
    }

    // Step 3: Generate PDF
    setProgress("pdf");
    try {
      // Capture chart as PNG if available
      let chartPng: string | undefined;
      if (chartRef.current) {
        try {
          const { toPng } = await import("html-to-image");
          chartPng = await toPng(chartRef.current, { quality: 0.95, pixelRatio: 2 });
        } catch { /* chart capture optional */ }
      }

      // Dynamic import to avoid SSR issues with react-pdf
      const { pdf } = await import("@react-pdf/renderer");
      const { ReportDocument } = await import("@/components/ai/ReportDocument");
      const { createElement } = await import("react");
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const doc = createElement(ReportDocument, {
        data,
        commentary: currentCommentary ?? "",
        anomalies: currentAnomalies,
        chartPng,
        generatedAt: new Date().toISOString(),
      }) as any;

      const blob = await pdf(doc).toBlob();

      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `headcount-report-${new Date().toISOString().split("T")[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      setProgress("done");
      setTimeout(() => setProgress("idle"), 2000);
    } catch (err) {
      console.error("PDF generation failed:", err);
      setProgress("idle");
    }
  }, [data, commentary, anomalies, setCommentary, setAnomalies, chartRef, progress]);

  return { generate, progress, isGenerating: progress !== "idle" && progress !== "done" };
}
