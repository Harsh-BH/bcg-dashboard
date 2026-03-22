"use client";

import { useCommentary } from "@/hooks/useCommentary";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Download, Loader2 } from "lucide-react";
import { useState } from "react";

export function CommentaryModal() {
  const { commentary, commentaryOpen, setCommentaryOpen, commentaryStreaming } = useCommentary();
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!commentary) return;
    navigator.clipboard.writeText(commentary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    if (!commentary) return;
    const blob = new Blob([commentary], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `headcount-commentary-${new Date().toISOString().split("T")[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Dialog open={commentaryOpen} onOpenChange={setCommentaryOpen}>
      <DialogContent className="max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader className="flex-row items-center justify-between">
          <DialogTitle className="flex items-center gap-2">
            {commentaryStreaming && <Loader2 size={16} className="animate-spin text-[hsl(var(--table-header))]" />}
            Headcount Commentary
          </DialogTitle>
          <div className="flex items-center gap-2 pr-8">
            <Button variant="outline" size="sm" onClick={handleCopy} disabled={!commentary}>
              <Copy size={13} className="mr-1.5" />
              {copied ? "Copied!" : "Copy"}
            </Button>
            <Button variant="outline" size="sm" onClick={handleDownload} disabled={!commentary}>
              <Download size={13} className="mr-1.5" />
              Export .md
            </Button>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto pr-1">
          {!commentary && commentaryStreaming && (
            <div className="flex items-center justify-center py-16 gap-3">
              <Loader2 size={20} className="animate-spin text-slate-400" />
              <span className="text-slate-500 text-sm">Generating commentary…</span>
            </div>
          )}
          {commentary && (
            <div className="prose prose-slate max-w-none prose-h2:text-base prose-h2:font-semibold prose-h2:text-slate-800 prose-h2:mt-5 prose-h2:mb-2 prose-p:text-sm prose-p:text-slate-700 prose-ul:text-sm prose-li:text-slate-700 prose-strong:text-slate-900">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {commentary}
              </ReactMarkdown>
            </div>
          )}
          {/* Blinking cursor while streaming */}
          {commentaryStreaming && (
            <span className="inline-block w-0.5 h-4 bg-[hsl(var(--table-header))] animate-pulse ml-0.5" />
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
