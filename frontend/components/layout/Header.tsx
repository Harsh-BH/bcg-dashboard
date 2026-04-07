"use client";

import { Search, Sun, Moon, Bell, LayoutGrid } from "lucide-react";
import { useDashboardStore } from "@/store/dashboardStore";

interface HeaderProps {
  currentTab: string;
  onToggleTheme: () => void;
  isDark: boolean;
}

export function Header({ currentTab, onToggleTheme, isDark }: HeaderProps) {
  const { anomalies } = useDashboardStore();

  return (
    <header className="h-14 border-b border-border bg-card/80 backdrop-blur-sm flex items-center justify-between px-6 sticky top-0 z-20">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm">
        <LayoutGrid size={16} className="text-muted-foreground" />
        <span className="text-muted-foreground">Dashboard</span>
        <span className="text-muted-foreground">/</span>
        <span className="font-medium text-foreground">{currentTab}</span>
      </div>

      {/* Search */}
      <div className="flex items-center gap-2 bg-muted/50 rounded-lg px-3 py-1.5 w-64 border border-border">
        <Search size={14} className="text-muted-foreground" />
        <span className="text-sm text-muted-foreground flex-1">Search</span>
        <kbd className="text-xs text-muted-foreground bg-background rounded px-1.5 py-0.5 border border-border font-mono">
          /
        </kbd>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        <button
          onClick={onToggleTheme}
          className="p-2 rounded-lg hover:bg-muted transition-colors"
          title={isDark ? "Switch to light mode" : "Switch to dark mode"}
        >
          {isDark ? (
            <Sun size={18} className="text-foreground" />
          ) : (
            <Moon size={18} className="text-muted-foreground" />
          )}
        </button>
        <button className="p-2 rounded-lg hover:bg-muted transition-colors relative">
          <Bell size={18} className="text-muted-foreground" />
          {anomalies.length > 0 && (
            <span className="absolute top-1 right-1 w-4 h-4 rounded-full bg-red-500 text-white text-[9px] font-bold flex items-center justify-center">
              {anomalies.length > 9 ? "9+" : anomalies.length}
            </span>
          )}
        </button>
      </div>
    </header>
  );
}
