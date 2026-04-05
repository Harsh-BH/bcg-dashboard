import { create } from "zustand";
import type { ProcessResponse, ChatMessage, Anomaly } from "@/lib/types";

interface DrillState {
  pairKey: string | null;
  rowLabel: string | null;
  column: "start" | "end" | "baseline" | "spartan_exit" | "bau" | "new_hire" | "endpoint" | null;
}

interface DashboardStore {
  data: ProcessResponse | null;
  setData: (d: ProcessResponse) => void;

  isLoading: boolean;
  setIsLoading: (v: boolean) => void;

  // selected pair for Tab1 preview
  previewStart: string | null;
  previewEnd: string | null;
  setPreview: (start: string, end: string) => void;

  // selected pair for Tab2 reconciliation
  reconBase: string | null;
  reconEnd: string | null;
  setRecon: (base: string, end: string) => void;

  // drill-down state
  drill: DrillState;
  setDrill: (d: DrillState) => void;
  clearDrill: () => void;

  // span tab: selected months, unknown grade choices
  spanMonths: string[];
  setSpanMonths: (months: string[]) => void;
  unknownGradeChoices: Record<string, "IC" | "TL" | "M1+">;
  setGradeChoice: (grade: string, choice: "IC" | "TL" | "M1+") => void;

  // ── AI: Chat ──────────────────────────────────────────────────────────────
  chatOpen: boolean;
  setChatOpen: (open: boolean) => void;
  chatMessages: ChatMessage[];
  appendChatMessage: (msg: ChatMessage) => void;
  updateLastAssistantMessage: (content: string) => void;
  clearChat: () => void;

  // ── AI: Commentary ────────────────────────────────────────────────────────
  commentary: string | null;
  setCommentary: (text: string | null) => void;
  commentaryOpen: boolean;
  setCommentaryOpen: (open: boolean) => void;
  commentaryStreaming: boolean;
  setCommentaryStreaming: (v: boolean) => void;

  // ── AI: Anomalies ─────────────────────────────────────────────────────────
  anomalies: Anomaly[];
  setAnomalies: (a: Anomaly[]) => void;
  anomalyLoading: boolean;
  setAnomalyLoading: (v: boolean) => void;
}

export const useDashboardStore = create<DashboardStore>((set) => ({
  data: null,
  setData: (d) => set({ data: d }),

  isLoading: false,
  setIsLoading: (v) => set({ isLoading: v }),

  previewStart: null,
  previewEnd: null,
  setPreview: (start, end) => set({ previewStart: start, previewEnd: end }),

  reconBase: null,
  reconEnd: null,
  setRecon: (base, end) => set({ reconBase: base, reconEnd: end }),

  drill: { pairKey: null, rowLabel: null, column: null },
  setDrill: (d) => set({ drill: d }),
  clearDrill: () => set({ drill: { pairKey: null, rowLabel: null, column: null } }),

  spanMonths: [],
  setSpanMonths: (months) => set({ spanMonths: months }),
  unknownGradeChoices: {},
  setGradeChoice: (grade, choice) =>
    set((s) => ({ unknownGradeChoices: { ...s.unknownGradeChoices, [grade]: choice } })),

  // ── AI: Chat ──────────────────────────────────────────────────────────────
  chatOpen: false,
  setChatOpen: (open) => set({ chatOpen: open }),
  chatMessages: [],
  appendChatMessage: (msg) =>
    set((s) => ({ chatMessages: [...s.chatMessages, msg] })),
  updateLastAssistantMessage: (content) =>
    set((s) => {
      const msgs = [...s.chatMessages];
      const last = msgs[msgs.length - 1];
      if (last?.role === "assistant") msgs[msgs.length - 1] = { ...last, content };
      return { chatMessages: msgs };
    }),
  clearChat: () => set({ chatMessages: [] }),

  // ── AI: Commentary ────────────────────────────────────────────────────────
  commentary: null,
  setCommentary: (text) => set({ commentary: text }),
  commentaryOpen: false,
  setCommentaryOpen: (open) => set({ commentaryOpen: open }),
  commentaryStreaming: false,
  setCommentaryStreaming: (v) => set({ commentaryStreaming: v }),

  // ── AI: Anomalies ─────────────────────────────────────────────────────────
  anomalies: [],
  setAnomalies: (a) => set({ anomalies: a }),
  anomalyLoading: false,
  setAnomalyLoading: (v) => set({ anomalyLoading: v }),
}));
