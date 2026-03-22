"use client";

import { useCallback, useMemo } from "react";
import { useDashboardStore } from "@/store/dashboardStore";
import { buildDashboardContext } from "@/lib/ai-context";
import { readStream } from "@/lib/claude-stream";
import type { ChatMessage } from "@/lib/types";

export function useChat() {
  const data = useDashboardStore((s) => s.data);
  const chatMessages = useDashboardStore((s) => s.chatMessages);
  const appendChatMessage = useDashboardStore((s) => s.appendChatMessage);
  const updateLastAssistantMessage = useDashboardStore((s) => s.updateLastAssistantMessage);
  const chatOpen = useDashboardStore((s) => s.chatOpen);
  const setChatOpen = useDashboardStore((s) => s.setChatOpen);
  const clearChat = useDashboardStore((s) => s.clearChat);

  const dashboardContext = useMemo(
    () => (data ? buildDashboardContext(data) : "No data loaded yet."),
    [data]
  );

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text.trim(),
        timestamp: Date.now(),
      };
      appendChatMessage(userMsg);

      // Placeholder assistant message that will be streamed into
      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: "",
        timestamp: Date.now(),
      };
      appendChatMessage(assistantMsg);

      // Build messages array for Claude (exclude the empty placeholder)
      const history = useDashboardStore
        .getState()
        .chatMessages.slice(0, -1) // all but the empty assistant placeholder
        .map((m) => ({ role: m.role, content: m.content }));

      let accumulated = "";
      try {
        for await (const chunk of readStream("/api/ai/chat", {
          messages: history,
          dashboardContext,
        })) {
          accumulated += chunk;
          updateLastAssistantMessage(accumulated);
        }
      } catch (err) {
        updateLastAssistantMessage(
          `Error: ${err instanceof Error ? err.message : "Something went wrong."}`
        );
      }
    },
    [appendChatMessage, updateLastAssistantMessage, dashboardContext]
  );

  return { chatMessages, sendMessage, chatOpen, setChatOpen, clearChat, hasData: !!data };
}
