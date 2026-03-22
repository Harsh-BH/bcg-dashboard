"use client";

import { useRef, useEffect, useState, KeyboardEvent } from "react";
import { useChat } from "@/hooks/useChat";
import { X, Send, Trash2, Bot, User, MessageSquare } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export function ChatDrawer() {
  const { chatMessages, sendMessage, chatOpen, setChatOpen, clearChat, hasData } = useChat();
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
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
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px]"
        onClick={() => setChatOpen(false)}
      />

      {/* Drawer */}
      <div className="fixed right-0 top-0 bottom-0 z-50 w-[420px] max-w-[95vw] flex flex-col bg-white shadow-2xl border-l border-slate-200 animate-in slide-in-from-right-8 duration-300">

        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-100 bg-gradient-to-r from-[hsl(var(--table-header))] to-[#7a0040]">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
              <Bot size={16} className="text-white" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-sm">HR Analytics Assistant</h2>
              <p className="text-white/60 text-xs">Ask anything about the dashboard data</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {chatMessages.length > 0 && (
              <button
                onClick={clearChat}
                className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                title="Clear chat"
              >
                <Trash2 size={14} />
              </button>
            )}
            <button
              onClick={() => setChatOpen(false)}
              className="p-1.5 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
            >
              <X size={16} />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {!hasData && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-3 py-12">
              <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center">
                <MessageSquare size={24} className="text-slate-400" />
              </div>
              <p className="text-slate-500 text-sm">Load dashboard data first, then ask me anything about your headcount.</p>
            </div>
          )}

          {hasData && chatMessages.length === 0 && (
            <div className="space-y-2 py-4">
              <p className="text-slate-400 text-xs text-center mb-4">Suggested questions</p>
              {[
                "Which department had the most exits?",
                "Summarize MoM headcount changes",
                "Are there any Spartan anomalies?",
                "What is the delivery headcount trend?",
              ].map((q) => (
                <button
                  key={q}
                  onClick={() => { setInput(q); textareaRef.current?.focus(); }}
                  className="w-full text-left text-xs text-slate-600 bg-slate-50 hover:bg-blue-50 hover:text-blue-700 border border-slate-200 hover:border-blue-200 rounded-xl px-3 py-2.5 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {chatMessages.map((msg) => (
            <div key={msg.id} className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}>
              {/* Avatar */}
              <div className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
                msg.role === "user"
                  ? "bg-[hsl(var(--table-header))]"
                  : "bg-slate-100"
              }`}>
                {msg.role === "user"
                  ? <User size={13} className="text-white" />
                  : <Bot size={13} className="text-slate-500" />
                }
              </div>

              {/* Bubble */}
              <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm ${
                msg.role === "user"
                  ? "bg-[hsl(var(--table-header))] text-white rounded-tr-sm"
                  : "bg-slate-50 border border-slate-100 text-slate-800 rounded-tl-sm"
              }`}>
                {msg.role === "assistant" && msg.content === "" ? (
                  <span className="flex gap-1 items-center py-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:0ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:150ms]" />
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce [animation-delay:300ms]" />
                  </span>
                ) : msg.role === "assistant" ? (
                  <div className="prose prose-sm prose-slate max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0.5">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {msg.content}
                    </ReactMarkdown>
                  </div>
                ) : (
                  msg.content
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="px-4 py-3 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-end gap-2 bg-white border border-slate-200 rounded-xl p-2 focus-within:border-[hsl(var(--table-header))] focus-within:ring-2 focus-within:ring-[hsl(var(--table-header))]/10 transition-all">
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={hasData ? "Ask about your headcount data…" : "Load data first…"}
              disabled={!hasData || isStreaming}
              className="flex-1 resize-none bg-transparent text-sm text-slate-800 placeholder-slate-400 outline-none min-h-[36px] max-h-[120px] py-1.5 px-1 disabled:opacity-50"
              style={{ fieldSizing: "content" } as React.CSSProperties}
            />
            <button
              onClick={handleSend}
              disabled={!input.trim() || !hasData || isStreaming}
              className="shrink-0 w-8 h-8 rounded-lg bg-[hsl(var(--table-header))] text-white flex items-center justify-center disabled:opacity-40 hover:opacity-90 transition-opacity"
            >
              <Send size={14} />
            </button>
          </div>
          <p className="text-slate-400 text-[10px] mt-1.5 text-center">Enter to send · Shift+Enter for new line</p>
        </div>
      </div>
    </>
  );
}
