import axios from "axios";
import type { ProcessResponse } from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({ baseURL: BASE_URL });

export interface ProcessPayload {
  hrmsFiles: File[];
  spartanFile?: File | null;
  payrollFile?: File | null;
  conneqtMappingFile?: File | null;
  payrollStart?: string;
  payrollEnd?: string;
}

export async function processFiles(payload: ProcessPayload): Promise<ProcessResponse> {
  const form = new FormData();

  for (const f of payload.hrmsFiles) {
    form.append("hrms_files", f, f.name);
  }
  if (payload.spartanFile) form.append("spartan_file", payload.spartanFile);
  if (payload.payrollFile) form.append("payroll_file", payload.payrollFile);
  if (payload.conneqtMappingFile) form.append("conneqt_mapping_file", payload.conneqtMappingFile);
  if (payload.payrollStart) form.append("payroll_start", payload.payrollStart);
  if (payload.payrollEnd) form.append("payroll_end", payload.payrollEnd);

  const { data } = await apiClient.post<ProcessResponse>("/api/process", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}
