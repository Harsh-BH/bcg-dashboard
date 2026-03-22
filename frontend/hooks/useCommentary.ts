"use client";

import { useCallback, useMemo } from "react";
import { useDashboardStore } from "@/store/dashboardStore";
import { buildDashboardContext } from "@/lib/ai-context";
import { readStream } from "@/lib/claude-stream";

export function useCommentary() {
  const data = useDashboardStore((s) => s.data);
  const commentary = useDashboardStore((s) => s.commentary);
  const setCommentary = useDashboardStore((s) => s.setCommentary);
  const commentaryOpen = useDashboardStore((s) => s.commentaryOpen);
  const setCommentaryOpen = useDashboardStore((s) => s.setCommentaryOpen);
  const commentaryStreaming = useDashboardStore((s) => s.commentaryStreaming);
  const setCommentaryStreaming = useDashboardStore((s) => s.setCommentaryStreaming);

  const dashboardContext = useMemo(
    () => (data ? buildDashboardContext(data) : ""),
    [data]
  );

  const generate = useCallback(async () => {
    if (!data || commentaryStreaming) return;
    setCommentary(null);
    setCommentaryStreaming(true);
    setCommentaryOpen(true);

    let accumulated = "";
    try {
      for await (const chunk of readStream("/api/ai/commentary", { dashboardContext })) {
        accumulated += chunk;
        setCommentary(accumulated);
      }
    } catch (err) {
      setCommentary(`Error generating commentary: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setCommentaryStreaming(false);
    }
  }, [data, commentaryStreaming, dashboardContext, setCommentary, setCommentaryStreaming, setCommentaryOpen]);

  return {
    commentary,
    commentaryOpen,
    setCommentaryOpen,
    commentaryStreaming,
    generate,
    hasData: !!data,
  };
}
