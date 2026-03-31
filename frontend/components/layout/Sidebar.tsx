"use client";

import { Fragment, useEffect, useRef, useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { useDashboardData } from "@/hooks/useDashboardData";
import { validateHrmsHeaders } from "@/lib/hrms-validator";
import type { ValidationResult } from "@/lib/types";
import {
  BarChart3, FolderOpen, Upload, X,
  AlertCircle, Loader2, FileSpreadsheet, CheckCircle2, ShieldAlert,
} from "lucide-react";
// ValidationResult.mappings is unused after validator simplification — kept for type compat

async function getFilesFromDrop(dt: DataTransfer): Promise<File[]> {
  return Array.from(dt.files).filter((f) => f.name.toLowerCase().endsWith(".xlsx"));
}

// ── Component ────────────────────────────────────────────────────────────────

export function Sidebar() {
  const [hrmsFiles, setHrmsFiles] = useState<File[]>([]);
  const [columnWarnings, setColumnWarnings] = useState<Map<string, ValidationResult>>(new Map());
  const [spartanFile, setSpartanFile] = useState<File | null>(null);
  const [payrollFile, setPayrollFile] = useState<File | null>(null);
  const [conneqtMappingFile, setConneqtMappingFile] = useState<File | null>(null);
  const [payrollStart, setPayrollStart] = useState("");
  const [payrollEnd,   setPayrollEnd]   = useState("");
  const [isDragOver,   setIsDragOver]   = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const d = new Date();
    setPayrollStart(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-01`);
    setPayrollEnd(d.toISOString().split("T")[0]);
  }, []);

  const { mutate, isPending, isError, error } = useDashboardData();

  // ── Add HRMS files, deduplicating ────────────────────────────────────────
  const addHrmsFiles = (files: File[]) => {
    const xlsx = files.filter((f) => f.name.toLowerCase().endsWith(".xlsx"));
    if (!xlsx.length) return;
    setValidationError(null);
    setHrmsFiles((prev) => {
      const existing = new Set(prev.map((f) => f.name));
      const newFiles = xlsx.filter((f) => !existing.has(f.name));
      runValidation(newFiles);
      return [...prev, ...newFiles].sort((a, b) => a.name.localeCompare(b.name));
    });
  };

  // ── File input (multi-select) ─────────────────────────────────────────────
  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    addHrmsFiles(Array.from(e.target.files ?? []));
    e.target.value = "";
  };

  // ── Drag-and-drop ────────────────────────────────────────────────────────
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    if (!e.currentTarget.contains(e.relatedTarget as Node)) setIsDragOver(false);
  };
  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = await getFilesFromDrop(e.dataTransfer);
    addHrmsFiles(files);
  };

  const removeHrms = (name: string) =>
    setHrmsFiles((prev) => prev.filter((f) => f.name !== name));

  // ── Validate headers for new files ──────────────────────────────────────
  const runValidation = useCallback(async (files: File[]) => {
    const results = await Promise.all(
      files.map(async (f) => {
        try { return [f.name, await validateHrmsHeaders(f)] as const; }
        catch { return null; }
      })
    );
    setColumnWarnings((prev) => {
      const next = new Map(prev);
      results.forEach((r) => { if (r) next.set(r[0], r[1]); });
      return next;
    });
  }, []);

  const clearAll = () => { setHrmsFiles([]); setColumnWarnings(new Map()); };

  const handleGenerate = () => {
    if (hrmsFiles.length < 2) {
      setValidationError("Need at least 2 HRMS snapshots.");
      return;
    }
    setValidationError(null);
    mutate({ hrmsFiles, spartanFile, payrollFile, conneqtMappingFile, payrollStart, payrollEnd });
  };

  const errorMsg =
    validationError ??
    (isError
      ? ((error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
          "Processing failed. Check your files and try again.")
      : null);

  return (
    <aside
      className="w-72 shrink-0 flex flex-col h-screen sticky top-0 overflow-y-auto"
      style={{ background: "linear-gradient(180deg, #1e293b 0%, #0f172a 100%)" }}
    >
      {/* ── Header ────────────────────────────────────────────── */}
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-2.5 mb-1">
          <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center shrink-0">
            <BarChart3 className="text-blue-400" size={18} />
          </div>
          <h1 className="text-white font-bold text-base leading-tight">Headcount Dashboard</h1>
        </div>
        <p className="text-slate-400 text-xs ml-[2.625rem]">BCG HR Analytics</p>
      </div>

      <Separator className="bg-slate-700/60" />

      <div className="px-5 py-4 flex flex-col gap-5 flex-1">

        {/* ── HRMS Folder ───────────────────────────────────────── */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <Label className="text-slate-200 font-semibold text-sm">
              HRMS Snapshots <span className="text-red-400">*</span>
            </Label>
            {hrmsFiles.length > 0 && (
              <button
                onClick={clearAll}
                className="text-slate-500 hover:text-red-400 text-xs flex items-center gap-1 transition-colors"
              >
                <X size={11} /> Clear all
              </button>
            )}
          </div>

          {/* Drop zone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={[
              "border-2 border-dashed rounded-xl p-5 text-center cursor-pointer",
              "transition-all duration-200 select-none",
              isDragOver
                ? "border-blue-400 bg-blue-500/15 scale-[1.01] ring-2 ring-blue-400/40"
                : "border-slate-600 hover:border-slate-400 hover:bg-slate-800/50",
            ].join(" ")}
          >
            {/* Hidden multi-file input */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".xlsx"
              multiple
              className="sr-only"
              onChange={handleFileInput}
            />

            <div className={`mx-auto mb-2 w-10 h-10 rounded-xl flex items-center justify-center ${
              isDragOver ? "bg-blue-500/20" : "bg-slate-700/60"
            }`}>
              <FolderOpen size={20} className={isDragOver ? "text-blue-400" : "text-slate-400"} />
            </div>
            <p className="text-slate-300 text-xs font-semibold">
              {isDragOver ? "Release to add files…" : "Drop HRMS files here"}
            </p>
            <p className="text-slate-500 text-xs mt-0.5">or click to browse (multi-select)</p>
            <p className="text-slate-600 text-xs mt-2 leading-relaxed">
              Any <span className="font-mono text-slate-500">.xlsx</span> files accepted
            </p>
          </div>

          {/* File list */}
          {hrmsFiles.length > 0 && (
            <ul className="mt-2 space-y-1">
              {hrmsFiles.map((f) => {
                const w = columnWarnings.get(f.name);
                const missing = w?.missing ?? [];
                return (
                  <Fragment key={f.name}>
                    <li className="flex items-center gap-1.5 bg-slate-800 rounded-lg px-2.5 py-1.5 animate-in fade-in-0 slide-in-from-top-1 duration-150">
                      <FileSpreadsheet size={13} className={missing.length ? "text-red-400 shrink-0" : (w?.recommended?.length ? "text-amber-400 shrink-0" : "text-emerald-400 shrink-0")} />
                      <span className="text-slate-300 text-xs flex-1 truncate">{f.name}</span>
                      <button
                        onClick={() => removeHrms(f.name)}
                        className="flex items-center justify-center w-5 h-5 rounded-full text-slate-500 hover:bg-slate-600 hover:text-red-400 transition-colors"
                      >
                        <X size={11} />
                      </button>
                    </li>
                    {missing.length > 0 && (
                      <li key={`${f.name}-error`} className="bg-red-900/30 border border-red-700/40 rounded-lg px-2.5 py-1.5 animate-in fade-in-0 duration-150">
                        <div className="flex items-start gap-1.5">
                          <ShieldAlert size={11} className="text-red-400 shrink-0 mt-0.5" />
                          <div className="text-red-300 text-[10px] leading-relaxed">
                            <div className="font-semibold mb-0.5">Required columns missing:</div>
                            {missing.map((m: string) => <div key={m}>• {m}</div>)}
                          </div>
                        </div>
                      </li>
                    )}
                    {missing.length === 0 && (w?.recommended ?? []).length > 0 && (
                      <li key={`${f.name}-rec`} className="bg-amber-900/20 border border-amber-700/30 rounded-lg px-2.5 py-1.5 animate-in fade-in-0 duration-150">
                        <div className="flex items-start gap-1.5">
                          <ShieldAlert size={11} className="text-amber-400 shrink-0 mt-0.5" />
                          <div className="text-amber-300 text-[10px] leading-relaxed">
                            <div className="font-semibold mb-0.5">Optional columns absent (reduced functionality):</div>
                            {(w?.recommended ?? []).map((m: string) => <div key={m}>• {m}</div>)}
                          </div>
                        </div>
                      </li>
                    )}
                  </Fragment>
                );
              })}
            </ul>
          )}

          {/* Status row */}
          {hrmsFiles.length > 0 && (
            <div className="mt-2">
              <p className="text-xs flex items-center gap-1.5">
                {hrmsFiles.length >= 2
                  ? <CheckCircle2 size={11} className="text-emerald-400 shrink-0" />
                  : <AlertCircle   size={11} className="text-amber-400 shrink-0" />
                }
                <span className={hrmsFiles.length >= 2 ? "text-emerald-400" : "text-amber-400"}>
                  {hrmsFiles.length} snapshot{hrmsFiles.length !== 1 ? "s" : ""} loaded
                  {hrmsFiles.length < 2 && " (need ≥ 2)"}
                </span>
              </p>
            </div>
          )}
        </div>

        <Separator className="bg-slate-700/60" />

        {/* ── Conneqt Mapping ───────────────────────────────────── */}
        <div>
          <Label className="text-slate-200 font-semibold text-sm mb-2 block">
            Conneqt Cost Mapping{" "}
            <span className="text-slate-500 font-normal">(optional)</span>
          </Label>
          <label className="flex items-center gap-2 cursor-pointer bg-slate-800 hover:bg-slate-700 rounded-xl px-3 py-2.5 transition-colors duration-150">
            <Upload size={14} className="text-slate-400 shrink-0" />
            <span className={`text-xs flex-1 truncate ${conneqtMappingFile ? "text-slate-200" : "text-slate-400"}`}>
              {conneqtMappingFile ? conneqtMappingFile.name : "Upload mapping .xlsx"}
            </span>
            {conneqtMappingFile && <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />}
            <input
              type="file" accept=".xlsx" className="sr-only"
              onChange={(e) => setConneqtMappingFile(e.target.files?.[0] ?? null)}
            />
          </label>
          {conneqtMappingFile && (
            <button
              onClick={() => setConneqtMappingFile(null)}
              className="text-xs text-slate-500 hover:text-red-400 mt-1.5 flex items-center gap-1 transition-colors"
            >
              <X size={11} /> Remove
            </button>
          )}
        </div>

        <Separator className="bg-slate-700/60" />

        {/* ── Spartan ───────────────────────────────────────────── */}
        <div>
          <Label className="text-slate-200 font-semibold text-sm mb-2 block">
            D2 Spartan{" "}
            <span className="text-slate-500 font-normal">(optional)</span>
          </Label>
          <label className="flex items-center gap-2 cursor-pointer bg-slate-800 hover:bg-slate-700 rounded-xl px-3 py-2.5 transition-colors duration-150">
            <Upload size={14} className="text-slate-400 shrink-0" />
            <span className={`text-xs flex-1 truncate ${spartanFile ? "text-slate-200" : "text-slate-400"}`}>
              {spartanFile ? spartanFile.name : "Upload Spartan .xlsx"}
            </span>
            {spartanFile && <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />}
            <input
              type="file" accept=".xlsx" className="sr-only"
              onChange={(e) => setSpartanFile(e.target.files?.[0] ?? null)}
            />
          </label>
          {spartanFile && (
            <button
              onClick={() => setSpartanFile(null)}
              className="text-xs text-slate-500 hover:text-red-400 mt-1.5 flex items-center gap-1 transition-colors"
            >
              <X size={11} /> Remove
            </button>
          )}
        </div>

        <Separator className="bg-slate-700/60" />

        {/* ── Payroll ───────────────────────────────────────────── */}
        <div>
          <Label className="text-slate-200 font-semibold text-sm mb-2 block">
            Payroll{" "}
            <span className="text-slate-500 font-normal">(optional)</span>
          </Label>
          <label className="flex items-center gap-2 cursor-pointer bg-slate-800 hover:bg-slate-700 rounded-xl px-3 py-2.5 transition-colors duration-150">
            <Upload size={14} className="text-slate-400 shrink-0" />
            <span className={`text-xs flex-1 truncate ${payrollFile ? "text-slate-200" : "text-slate-400"}`}>
              {payrollFile ? payrollFile.name : "Upload Payroll .xlsx"}
            </span>
            {payrollFile && <CheckCircle2 size={13} className="text-emerald-400 shrink-0" />}
            <input
              type="file" accept=".xlsx" className="sr-only"
              onChange={(e) => setPayrollFile(e.target.files?.[0] ?? null)}
            />
          </label>
          {payrollFile && (
            <button
              onClick={() => setPayrollFile(null)}
              className="text-xs text-slate-500 hover:text-red-400 mt-1.5 flex items-center gap-1 transition-colors"
            >
              <X size={11} /> Remove
            </button>
          )}

          <div className="mt-3 space-y-2">
            <div>
              <Label className="text-slate-400 text-xs mb-1 block">Cycle start</Label>
              <Input
                type="date" value={payrollStart}
                onChange={(e) => setPayrollStart(e.target.value)}
                className="bg-slate-800 border-slate-600 text-slate-200 text-sm h-9 focus:border-blue-500 transition-colors"
              />
            </div>
            <div>
              <Label className="text-slate-400 text-xs mb-1 block">Cycle end</Label>
              <Input
                type="date" value={payrollEnd}
                onChange={(e) => setPayrollEnd(e.target.value)}
                className="bg-slate-800 border-slate-600 text-slate-200 text-sm h-9 focus:border-blue-500 transition-colors"
              />
            </div>
          </div>
        </div>

        {/* ── Error ─────────────────────────────────────────────── */}
        {errorMsg && (
          <Alert className="bg-red-900/40 border-red-700/60 py-2.5 px-3">
            <AlertCircle size={14} className="text-red-400" />
            <AlertDescription className="text-xs text-red-300 ml-1">{errorMsg}</AlertDescription>
          </Alert>
        )}

        {/* ── Generate ──────────────────────────────────────────── */}
        <div className="mt-auto pt-2">
          <Button
            onClick={handleGenerate}
            disabled={isPending || hrmsFiles.length < 2}
            className="w-full font-semibold text-sm py-5 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 shadow-md hover:shadow-lg transition-all duration-200 text-white border-0 disabled:from-slate-700 disabled:to-slate-700 disabled:text-slate-500 disabled:shadow-none"
          >
            {isPending ? (
              <><Loader2 size={15} className="animate-spin mr-2" />Processing…</>
            ) : (
              "Generate Dashboard"
            )}
          </Button>
          {hrmsFiles.length >= 2 && !isPending && (
            <p className="text-center text-slate-500 text-xs mt-2">
              {hrmsFiles.length} snapshots ready
            </p>
          )}
        </div>
      </div>
    </aside>
  );
}
