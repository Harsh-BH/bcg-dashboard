"use client";

import { useRef, useEffect, useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertTriangle, MessageSquare, Sparkles, FileDown, Loader2, CheckCircle2 } from "lucide-react";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { ActivityPanel } from "@/components/layout/ActivityPanel";
import { StatCards } from "@/components/dashboard/StatCards";
import { OverallView } from "@/components/tabs/OverallView";
import { HrmsWalk } from "@/components/tabs/HrmsWalk";
import { SpanMovement } from "@/components/tabs/SpanMovement";
import { SpartanChecks } from "@/components/tabs/SpartanChecks";
import { ChatDrawer } from "@/components/ai/ChatDrawer";
import { CommentaryModal } from "@/components/ai/CommentaryModal";
import { useDashboardStore } from "@/store/dashboardStore";
import { useCommentary } from "@/hooks/useCommentary";
import { useReportGeneration } from "@/hooks/useReportGeneration";

const TABS = [
  { value: "overall",    label: "Overall" },
  { value: "hrms-walk",  label: "HRMS Walk" },
  { value: "span",       label: "Span / Movement" },
  { value: "spartan",    label: "Spartan / Payroll" },
] as const;

function AnomalyBadge({ count }: { count: number }) {
  if (!count) return null;
  return (
    <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold">
      {count > 9 ? "9+" : count}
    </span>
  );
}

function DashboardContent({ onTabChange }: { onTabChange: (tab: string) => void }) {
  const { data, anomalies, chatOpen, setChatOpen } = useDashboardStore();
  const { generate: generateCommentary, commentaryStreaming } = useCommentary();

  const chartRef = useRef<HTMLDivElement>(null);
  const { generate: generateReport, progress: reportProgress, isGenerating } = useReportGeneration(chartRef);

  const anomalyCount = (tab: string) => anomalies.filter((a) => a.tab === tab).length;

  const progressLabels: Record<string, string> = {
    commentary: "Writing commentary…",
    anomalies:  "Detecting anomalies…",
    pdf:        "Generating PDF…",
    done:       "Downloaded!",
  };

  return (
    <>
    <div className="flex flex-1 min-h-0">
      <div className="flex-1 min-w-0 overflow-y-auto p-6 lg:p-8">
        <div className="space-y-6 max-w-7xl mx-auto">
            {/* Validation warnings */}
            {data?.validation_warnings && data.validation_warnings.length > 0 && (
              <Alert className="border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-800">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <AlertDescription className="text-amber-700 dark:text-amber-300 text-xs">
                  <ul className="list-disc list-inside space-y-0.5">
                    {data.validation_warnings.map((w, i) => (
                      <li key={i}>
                        <span className="font-mono">{w.file}</span>: {w.message}
                      </li>
                    ))}
                  </ul>
                </AlertDescription>
              </Alert>
            )}

            {/* Stat cards */}
            {data && <StatCards trend={data.trend} />}

            {/* AI action bar */}
            <div className="flex items-center justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={generateCommentary}
                disabled={commentaryStreaming}
                className="gap-1.5 text-xs border-border hover:border-primary hover:text-primary"
              >
                {commentaryStreaming
                  ? <Loader2 size={13} className="animate-spin" />
                  : <Sparkles size={13} />
                }
                Generate Insights
              </Button>

              <Button
                variant="outline"
                size="sm"
                onClick={generateReport}
                disabled={isGenerating}
                className="gap-1.5 text-xs border-border hover:border-primary hover:text-primary"
              >
                {reportProgress === "done"
                  ? <CheckCircle2 size={13} className="text-emerald-500" />
                  : isGenerating
                    ? <Loader2 size={13} className="animate-spin" />
                    : <FileDown size={13} />
                }
                {isGenerating ? (progressLabels[reportProgress] ?? "Generating…") : "Export Report"}
              </Button>
            </div>

            <Tabs defaultValue="overall" onValueChange={onTabChange}>
              <TabsList className="mb-4 bg-card border border-border rounded-xl shadow-sm p-1 gap-0.5">
                {TABS.map((t) => (
                  <TabsTrigger
                    key={t.value}
                    value={t.value}
                    className="rounded-lg text-sm font-medium transition-all duration-150 data-[state=active]:bg-primary data-[state=active]:text-primary-foreground data-[state=active]:shadow-sm hover:bg-muted data-[state=active]:hover:bg-primary"
                  >
                    {t.label}
                    <AnomalyBadge count={anomalyCount(t.value)} />
                  </TabsTrigger>
                ))}
              </TabsList>

              <TabsContent value="overall" className="animate-in fade-in-0 slide-in-from-bottom-1 duration-200">
                <div ref={chartRef}>
                  <OverallView />
                </div>
              </TabsContent>
              <TabsContent value="hrms-walk" className="animate-in fade-in-0 slide-in-from-bottom-1 duration-200">
                <HrmsWalk />
              </TabsContent>
              <TabsContent value="span" className="animate-in fade-in-0 slide-in-from-bottom-1 duration-200">
                <SpanMovement />
              </TabsContent>
              <TabsContent value="spartan" className="animate-in fade-in-0 slide-in-from-bottom-1 duration-200">
                <SpartanChecks />
              </TabsContent>
            </Tabs>
          </div>
        </div>

        {/* Right activity panel */}
        <ActivityPanel />
      </div>

      {/* Floating chat button */}
      <button
        onClick={() => setChatOpen(!chatOpen)}
        className="fixed bottom-6 right-6 z-30 w-14 h-14 rounded-2xl text-white flex items-center justify-center transition-all duration-200 hover:scale-105 hover:-translate-y-0.5 active:scale-95 group"
        style={{ background: "linear-gradient(135deg, #5A002F 0%, #8B0045 100%)", boxShadow: "0 8px 24px rgba(90,0,47,0.45), 0 2px 8px rgba(0,0,0,0.15)" }}
        title="Open AI chat"
      >
        <MessageSquare size={20} className="transition-transform duration-200 group-hover:scale-110" />
        {anomalies.length > 0 && (
          <span className="absolute -top-1.5 -right-1.5 min-w-[20px] h-5 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center px-1 shadow-md ring-2 ring-white">
            {anomalies.length > 9 ? "9+" : anomalies.length}
          </span>
        )}
      </button>
    </>
  );
}

const LOADING_VERBS = [
  "Crunching data…",
  "Parsing snapshots…",
  "Normalizing columns…",
  "Classifying buckets…",
  "Building hierarchy tables…",
  "Computing headcount trends…",
  "Reconciling movements…",
  "Analyzing span of control…",
  "Calculating MoM changes…",
  "Preparing drill-down index…",
  "Almost there…",
];

function LoadingScreen() {
  const [verbIdx, setVerbIdx] = useState(0);
  const [dots, setDots] = useState(0);

  useEffect(() => {
    const verbTimer = setInterval(() => {
      setVerbIdx((i) => (i + 1) % LOADING_VERBS.length);
    }, 1800);
    const dotTimer = setInterval(() => {
      setDots((d) => (d + 1) % 4);
    }, 400);
    return () => { clearInterval(verbTimer); clearInterval(dotTimer); };
  }, []);

  return (
    <div className="flex flex-col items-center justify-center h-full min-h-[60vh] gap-6 select-none">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-4 border-muted" />
        <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary animate-spin" />
      </div>
      <div className="text-center">
        <p className="text-foreground font-semibold text-base tabular-nums min-w-[220px]">
          {LOADING_VERBS[verbIdx].replace("…", "").trimEnd()}
          <span className="text-primary">{".".repeat(dots + 1)}</span>
        </p>
        <p className="text-muted-foreground text-xs mt-1">Processing your HRMS snapshots</p>
      </div>
      <div className="w-48 h-1 bg-muted rounded-full overflow-hidden">
        <div className="h-full bg-primary rounded-full animate-[loading-bar_2s_ease-in-out_infinite]" />
      </div>
    </div>
  );
}

export default function Home() {
  const { data, isLoading } = useDashboardStore();

  // Dark mode state — lifted here so Header always has it
  const [isDark, setIsDark] = useState(false);
  useEffect(() => {
    setIsDark(document.documentElement.classList.contains("dark"));
  }, []);
  const toggleTheme = () => {
    const next = !isDark;
    setIsDark(next);
    document.documentElement.classList.toggle("dark", next);
  };

  const [activeTab, setActiveTab] = useState("overall");
  const currentTabLabel = TABS.find((t) => t.value === activeTab)?.label ?? "Overview";

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1 min-w-0 flex flex-col">
        <Header currentTab={data ? currentTabLabel : "Home"} onToggleTheme={toggleTheme} isDark={isDark} />

        {isLoading ? (
          <main className="flex-1 p-6 lg:p-8">
            <LoadingScreen />
          </main>
        ) : !data ? (
          <main className="flex-1 flex items-center justify-center p-6 lg:p-8">
            <div className="rounded-2xl border border-border bg-card p-10 shadow-sm max-w-md text-center">
              <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mx-auto mb-4">
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="hsl(var(--primary))" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                  <polyline points="14 2 14 8 20 8"/>
                  <line x1="16" y1="13" x2="8" y2="13"/>
                  <line x1="16" y1="17" x2="8" y2="17"/>
                  <polyline points="10 9 9 9 8 9"/>
                </svg>
              </div>
              <h2 className="text-foreground font-semibold text-lg mb-2">No data loaded</h2>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Upload at least 2 HRMS snapshot files using the sidebar, then click{" "}
                <strong className="text-foreground">Generate Dashboard</strong>.
              </p>
            </div>
          </main>
        ) : (
          <DashboardContent onTabChange={setActiveTab} />
        )}
      </div>

      {/* AI overlays */}
      <ChatDrawer />
      <CommentaryModal />
    </div>
  );
}
