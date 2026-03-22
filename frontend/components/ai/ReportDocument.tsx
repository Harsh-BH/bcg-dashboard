import React from "react";
import {
  Document,
  Page,
  Text,
  View,
  Image,
  StyleSheet,
  Font,
} from "@react-pdf/renderer";
import type { ProcessResponse, Anomaly } from "@/lib/types";

// Use built-in Helvetica (no external font needed)
const styles = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    backgroundColor: "#ffffff",
    paddingHorizontal: 48,
    paddingVertical: 48,
    fontSize: 10,
    color: "#1e293b",
  },
  // Header
  header: {
    backgroundColor: "#5A002F",
    marginHorizontal: -48,
    marginTop: -48,
    paddingHorizontal: 48,
    paddingVertical: 24,
    marginBottom: 28,
  },
  headerTitle: {
    color: "#ffffff",
    fontSize: 20,
    fontFamily: "Helvetica-Bold",
    marginBottom: 4,
  },
  headerSub: {
    color: "rgba(255,255,255,0.7)",
    fontSize: 10,
  },
  // Section
  sectionTitle: {
    fontSize: 13,
    fontFamily: "Helvetica-Bold",
    color: "#5A002F",
    borderBottomWidth: 1,
    borderBottomColor: "#e2e8f0",
    paddingBottom: 4,
    marginBottom: 10,
    marginTop: 20,
  },
  // Text
  body: { fontSize: 10, color: "#334155", lineHeight: 1.6 },
  bold: { fontFamily: "Helvetica-Bold" },
  // Overview table
  table: { marginBottom: 12 },
  tableRow: { flexDirection: "row", borderBottomWidth: 1, borderBottomColor: "#f1f5f9" },
  tableHeaderRow: { flexDirection: "row", backgroundColor: "#5A002F" },
  tableHeader: { color: "#ffffff", fontFamily: "Helvetica-Bold", fontSize: 9, padding: 6, flex: 1 },
  tableCell: { fontSize: 9, padding: 6, flex: 1, color: "#334155" },
  // Anomaly
  anomalyHigh:   { backgroundColor: "#fef2f2", borderLeftWidth: 3, borderLeftColor: "#ef4444", padding: 8, marginBottom: 6, borderRadius: 4 },
  anomalyMedium: { backgroundColor: "#fffbeb", borderLeftWidth: 3, borderLeftColor: "#f59e0b", padding: 8, marginBottom: 6, borderRadius: 4 },
  anomalyLow:    { backgroundColor: "#eff6ff", borderLeftWidth: 3, borderLeftColor: "#3b82f6", padding: 8, marginBottom: 6, borderRadius: 4 },
  anomalyTitle:  { fontFamily: "Helvetica-Bold", fontSize: 9, marginBottom: 3 },
  anomalyExpl:   { fontSize: 8.5, color: "#475569", lineHeight: 1.5 },
  // Footer
  footer: { position: "absolute", bottom: 24, left: 48, right: 48, flexDirection: "row", justifyContent: "space-between" },
  footerText: { fontSize: 8, color: "#94a3b8" },
});

// Simple markdown stripping for plain text rendering
function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s+/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .replace(/\*(.*?)\*/g, "$1")
    .replace(/^[-*+]\s+/gm, "• ")
    .replace(/`([^`]+)`/g, "$1")
    .trim();
}

interface Props {
  data: ProcessResponse;
  commentary: string;
  anomalies: Anomaly[];
  chartPng?: string;
  generatedAt: string;
}

export function ReportDocument({ data, commentary, anomalies, chartPng, generatedAt }: Props) {
  const dateStr = new Date(generatedAt).toLocaleDateString("en-IN", {
    year: "numeric", month: "long", day: "numeric",
  });

  return (
    <Document title="BCG Headcount Report" author="BCG HR Analytics">
      <Page size="A4" style={styles.page}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Headcount Dashboard Report</Text>
          <Text style={styles.headerSub}>BCG HR Analytics · Generated {dateStr}</Text>
        </View>

        {/* Snapshot summary */}
        <Text style={styles.sectionTitle}>Snapshots Analysed</Text>
        <Text style={styles.body}>
          {data.snapshots.map((s) => s.label).join("  →  ")}
        </Text>

        {/* Chart */}
        {chartPng && (
          <>
            <Text style={styles.sectionTitle}>Headcount Trend</Text>
            <Image src={chartPng} style={{ width: "100%", height: 200, objectFit: "contain", marginBottom: 8 }} />
          </>
        )}

        {/* Overview table */}
        <Text style={styles.sectionTitle}>Month-over-Month Overview</Text>
        <View style={styles.table}>
          <View style={styles.tableHeaderRow}>
            {["Period", "Start HC", "End HC", "Change", "% Change"].map((h) => (
              <Text key={h} style={styles.tableHeader}>{h}</Text>
            ))}
          </View>
          {data.overview_table.map((r, i) => (
            <View key={i} style={[styles.tableRow, i % 2 === 1 ? { backgroundColor: "#f8fafc" } : {}]}>
              <Text style={styles.tableCell}>{r.start_month} → {r.end_month}</Text>
              <Text style={styles.tableCell}>{r.start_hc.toLocaleString()}</Text>
              <Text style={styles.tableCell}>{r.end_hc.toLocaleString()}</Text>
              <Text style={styles.tableCell}>{r.abs_change >= 0 ? "+" : ""}{r.abs_change}</Text>
              <Text style={styles.tableCell}>{r.pct_change != null ? r.pct_change.toFixed(1) + "%" : "N/A"}</Text>
            </View>
          ))}
        </View>

        {/* Commentary */}
        {commentary && (
          <>
            <Text style={styles.sectionTitle}>Executive Commentary</Text>
            <Text style={styles.body}>{stripMarkdown(commentary)}</Text>
          </>
        )}

        {/* Anomalies */}
        {anomalies.length > 0 && (
          <>
            <Text style={styles.sectionTitle}>Anomalies & Watch Items</Text>
            {anomalies.map((a, i) => {
              const s = a.severity === "high" ? styles.anomalyHigh : a.severity === "medium" ? styles.anomalyMedium : styles.anomalyLow;
              return (
                <View key={i} style={s}>
                  <Text style={styles.anomalyTitle}>[{a.severity.toUpperCase()}] {a.title}</Text>
                  <Text style={styles.anomalyExpl}>{a.explanation}</Text>
                </View>
              );
            })}
          </>
        )}

        {/* Footer */}
        <View style={styles.footer} fixed>
          <Text style={styles.footerText}>BCG Headcount Dashboard · Confidential</Text>
          <Text style={styles.footerText} render={({ pageNumber, totalPages }) => `${pageNumber} / ${totalPages}`} />
        </View>
      </Page>
    </Document>
  );
}
