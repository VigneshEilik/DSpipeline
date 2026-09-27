"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Database,
  FlaskConical,
  Boxes,
  Rocket,
  Sparkles,
  Activity,
  Settings,
  Menu,
  ChevronDown,
  Bell,
  Search,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { api } from "@/services/api";

const NAV_ITEMS = [
  { href: "/overview", label: "Overview", icon: LayoutDashboard },
  { href: "/datasets", label: "Datasets", icon: Database },
  { href: "/experiments", label: "Experiments", icon: FlaskConical },
  { href: "/models", label: "Model Registry", icon: Boxes },
  { href: "/deployments", label: "Deployments", icon: Rocket },
  { href: "/predictions", label: "Inference & Predictions", icon: Sparkles },
  { href: "/monitoring", label: "Observability & Drift", icon: Activity },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    // Bootstrap dev user automatically if not authenticated
    async function initAuth() {
      try {
        const devToken = await api.bootstrapDev();
        api.setToken(devToken.access_token);
        if (devToken.workspace_id) {
          api.setWorkspaceId(devToken.workspace_id);
        }
        const profile = await api.getMe();
        setUserProfile(profile);
        setBackendHealthy(true);
      } catch (err) {
        console.error("Auth init error:", err);
        setBackendHealthy(false);
      }
    }
    initAuth();
  }, []);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Sidebar Drawer */}
      <aside
        className={`flex flex-col border-r border-outline-variant/30 bg-surface transition-all duration-200 z-30 ${
          collapsed ? "w-20" : "w-64"
        }`}
      >
        {/* Brand Header */}
        <div className="flex h-16 items-center px-4 justify-between border-b border-outline-variant/20">
          <Link href="/overview" className="flex items-center gap-3 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-primary text-primary-foreground font-bold shadow-sm">
              M
            </div>
            {!collapsed && (
              <span className="font-semibold text-base tracking-tight text-foreground whitespace-nowrap">
                ModelOps Studio
              </span>
            )}
          </Link>
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="rounded-lg p-1.5 text-foreground/60 hover:bg-surface-container hover:text-foreground transition"
            title="Toggle Sidebar"
          >
            <Menu className="h-4 w-4" />
          </button>
        </div>

        {/* Workspace Chip */}
        {!collapsed && userProfile && userProfile.workspaces?.length > 0 && (
          <div className="px-4 py-3 border-b border-outline-variant/15">
            <div className="flex items-center justify-between px-3 py-2 rounded-xl bg-surface-container text-xs font-medium text-foreground/80">
              <span className="truncate max-w-[150px]">
                {userProfile.workspaces[0].name}
              </span>
              <span className="px-1.5 py-0.5 rounded text-[10px] bg-primary-container text-primary-onContainer font-semibold">
                {userProfile.workspaces[0].role}
              </span>
            </div>
          </div>
        )}

        {/* Navigation Items */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-1">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || (item.href !== "/overview" && pathname.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-full text-xs font-medium transition-all ${
                  active
                    ? "bg-primary-container text-primary-onContainer font-semibold shadow-xs"
                    : "text-foreground/70 hover:bg-surface-container hover:text-foreground"
                }`}
                title={collapsed ? item.label : undefined}
              >
                <Icon className={`h-4 w-4 shrink-0 ${active ? "text-primary" : "text-foreground/60"}`} />
                {!collapsed && <span className="truncate">{item.label}</span>}
              </Link>
            );
          })}
        </nav>

        {/* System Health Status Footer */}
        <div className="p-4 border-t border-outline-variant/20 text-xs">
          <div className="flex items-center gap-2 text-foreground/60">
            {backendHealthy ? (
              <>
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
                {!collapsed && <span className="truncate">API v1 Connected</span>}
              </>
            ) : (
              <>
                <span className="h-2 w-2 rounded-full bg-amber-500 shrink-0" />
                {!collapsed && <span className="truncate">Connecting to API...</span>}
              </>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top App Bar */}
        <header className="flex h-16 items-center justify-between border-b border-outline-variant/20 bg-surface px-6">
          <div className="flex items-center gap-3 text-sm text-foreground/70">
            <span className="font-semibold text-foreground capitalize">
              {pathname.replace("/(dashboard)/", "").replace("/", "") || "Overview"}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-foreground/40" />
              <input
                type="text"
                placeholder="Search models, runs..."
                className="w-56 rounded-full bg-surface-container py-1.5 pl-9 pr-4 text-xs text-foreground placeholder-foreground/40 border border-transparent focus:border-primary focus:outline-none"
              />
            </div>

            <button className="rounded-full p-2 text-foreground/60 hover:bg-surface-container hover:text-foreground transition">
              <Bell className="h-4 w-4" />
            </button>

            {userProfile && (
              <div className="flex items-center gap-2 pl-2 border-l border-outline-variant/30">
                <div className="h-7 w-7 rounded-full bg-primary/20 text-primary flex items-center justify-center font-bold text-xs">
                  {userProfile.full_name?.charAt(0) || "U"}
                </div>
                <span className="hidden sm:inline text-xs font-medium text-foreground">
                  {userProfile.full_name}
                </span>
              </div>
            )}
          </div>
        </header>

        {/* Dynamic Route Content */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="mx-auto max-w-7xl">{children}</div>
        </main>
      </div>
    </div>
  );
}
