"use client";

import { useRef, useEffect, useState, KeyboardEvent } from "react";
import { useChat } from "@/hooks/useChat";
import { X, Send, Trash2, Bot, User, MessageSquare, Sparkles } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const SUGGESTED = [
  "Which department had the most exits?",
  "Summarize MoM headcount changes",
  "Are there any Spartan anomalies?",
  "What is the delivery headcount trend?",
];

export function ChatDrawer() {
  const { chatMessages, sendMessage, chatOpen, setChatOpen, clearChat, hasData } = useChat();
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages]);

  const handleSend = async () => {
    if (!input.trim() || isStreaming) return;
    const text = input.trim();
    setInput("");
    setIsStreaming(true);
    await sendMessage(text);
    setIsStreaming(false);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!chatOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40 bg-black/30 backdrop-blur-sm"
        onClick={() => setChatOpen(false)}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 z-50 w-[440px] max-w-[96vw] flex flex-col shadow-2xl animate-in slide-in-from-right-6 duration-300 ease-out bg-background"
      >

        {/* Header */}
        <div className="relative flex items-center justify-between px-5 py-4 overflow-hidden"
          style={{ background: "linear-gradient(135deg, #5A002F 0%, #8B0045 60%, #a8005a 100%)" }}
        >
          {/* subtle radial glow */}
          <div className="absolute inset-0 opacity-20"
            style={{ background: "radial-gradient(ellipse at 20% 50%, #fff 0%, transparent 70%)" }}
          />
          <div className="relative flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-white/15 border border-white/20 flex items-center justify-center shadow-inner">
              <Sparkles size={16} className="text-white" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-sm leading-tight">HR Analytics Assistant</h2>
              <p className="text-white/55 text-[11px] mt-0.5">Powered by GPT-4o · Ask anything</p>
            </div>
          </div>
          <div className="relative flex items-center gap-1">
            {chatMessages.length > 0 && (
              <button
                onClick={clearChat}
                className="p-2 rounded-lg text-white/50 hover:text-white hover:bg-white/15 transition-all duration-150"
                title="Clear chat"
              >
                <Trash2 size={14} />
              </button>
            )}
            <button
              onClick={() => setChatOpen(false)}
              className="p-2 rounded-lg text-white/50 hover:text-white hover:bg-white/15 transition-all duration-150"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-5 space-y-5 scroll-smooth">

          {/* Empty — no data */}
          {!hasData && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4 py-16">
              <div className="w-16 h-16 rounded-2xl bg-card border border-border shadow-sm flex items-center justify-center">
                <MessageSquare size={26} className="text-muted-foreground" />
              </div>
              <div>
                <p className="text-foreground text-sm font-medium">No data loaded yet</p>
                <p className="text-muted-foreground text-xs mt-1">Upload HRMS files and generate the dashboard first.</p>
              </div>
            </div>
          )}

          {/* Suggested questions */}
          {hasData && chatMessages.length === 0 && (
            <div className="space-y-2 pt-2">
              <p className="text-muted-foreground text-[11px] text-center font-medium tracking-wide uppercase mb-4">
                Suggested questions
              </p>
              {SUGGESTED.map((q) => (
                <button
                  key={q}
                  onClick={() => { setInput(q); textareaRef.current?.focus(); }}
                  className="w-full text-left text-xs text-foreground bg-card hover:bg-rose-50 hover:text-[#5A002F] border border-border hover:border-rose-200 rounded-xl px-4 py-3 transition-all duration-150 shadow-sm hover:shadow-md"
                >
                  <span className="mr-2 opacity-40">→</span>{q}
                </button>
              ))}
            </div>
          )}

          {/* Messages */}
          {chatMessages.map((msg) => (
            <div key={msg.id} className={`flex gap-2.5 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>

              {/* Avatar */}
              <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ring-2 ${
                msg.role === "user"
                  ? "ring-[#5A002F]/20"
                  : "ring-border"
              }`}
                style={msg.role === "user"
                  ? { background: "linear-gradient(135deg, #5A002F, #8B0045)" }
                  : { background: "hsl(var(--muted))" }
                }
              >
                {msg.role === "user"
                  ? <User size={12} className="text-white" />
                  : <Bot size={12} className="text-muted-foreground" />
                }
              </div>

              {/* Bubble */}
              <div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm shadow-sm ${
                msg.role === "user"
                  ? "text-white rounded-tr-sm"
                  : "bg-card border border-border text-foreground rounded-tl-sm"
              }`}
                style={msg.role === "user"
                  ? { background: "linear-gradient(135deg, #5A002F, #8B0045)" }
                  : undefined
                }
              >
                {msg.role === "assistant" && msg.content === "" ? (
                  <span className="flex gap-1.5 items-center py-0.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:120ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-muted-foreground animate-bounce [animation-delay:240ms]" />
                  </span>
                ) : msg.role === "assistant" ? (
                  <div className="prose prose-sm prose-slate dark:prose-invert max-w-none
                    prose-p:my-1 prose-p:leading-relaxed
                    prose-ul:my-1.5 prose-li:my-0.5
                    prose-strong:text-foreground prose-strong:font-semibold
                    prose-code:bg-muted prose-code:px-1 prose-code:rounded prose-code:text-xs">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  <span className="leading-relaxed">{msg.content}</span>
                )}
              </div>
            </div>
          ))}

          <div ref={bottomRef} />
        </div>

        {/* Input bar */}
        <div className="px-4 pb-4 pt-3 border-t border-border/70 bg-card/60 backdrop-blur-sm">
          <div className={`flex items-end gap-2 bg-card border rounded-2xl px-3 py-2 shadow-sm transition-all duration-200 ${
            isStreaming ? "border-border" : "border-border focus-within:border-[#5A002F]/40 focus-within:shadow-md focus-within:ring-2 focus-within:ring-[#5A002F]/8"
          }`}>
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasData ? "Ask about your headcount data…" : "Load data first…"}
              disabled={!hasData || isStreaming}
              className="flex-1 resize-none bg-transparent text-sm text-foreground placeholder-muted-foreground outline-none min-h-[34px] max-h-[120px] py-1.5 px-1 disabled:opacity-40 leading-relaxed"
              style={{ fieldSizing: "content" } as React.CSSProperties}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !hasData || isStreaming}
              className="shrink-0 w-8 h-8 rounded-xl text-white flex items-center justify-center disabled:opacity-30 transition-all duration-150 hover:scale-105 active:scale-95"
              style={{ background: "linear-gradient(135deg, #5A002F, #8B0045)" }}
            >
              <Send size={13} />
            </button>
          </div>
          <p className="text-muted-foreground text-[10px] mt-2 text-center">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </>
  );
}
