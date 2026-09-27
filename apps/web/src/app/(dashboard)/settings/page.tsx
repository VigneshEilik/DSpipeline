"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Settings,
  Users,
  UserPlus,
  Shield,
  HardDrive,
  Database,
  Moon,
  Sun,
  Loader2,
} from "lucide-react";
import { api } from "@/services/api";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [addMemberOpen, setAddMemberOpen] = useState(false);
  const [memberEmail, setMemberEmail] = useState("");
  const [memberRole, setMemberRole] = useState("DATA_SCIENTIST");
  const [theme, setTheme] = useState("light");

  const { data: userProfile } = useQuery({
    queryKey: ["user-profile"],
    queryFn: () => api.getMe(),
  });

  const activeWorkspace = userProfile?.workspaces?.[0];

  const { data: workspaceDetail, isLoading: loadingWs } = useQuery({
    queryKey: ["workspace-detail", activeWorkspace?.id],
    queryFn: () => (activeWorkspace ? api.getWorkspace(activeWorkspace.id) : null),
    enabled: !!activeWorkspace,
  });

  const addMemberMutation = useMutation({
    mutationFn: () =>
      api.addMember(activeWorkspace.id, {
        email: memberEmail,
        role: memberRole,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workspace-detail", activeWorkspace?.id] });
      setAddMemberOpen(false);
      setMemberEmail("");
    },
  });

  const toggleTheme = () => {
    const nextTheme = theme === "light" ? "dark" : "light";
    setTheme(nextTheme);
    if (typeof document !== "undefined") {
      document.documentElement.classList.toggle("dark", nextTheme === "dark");
    }
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Workspace Settings & Team Access</h1>
        <p className="text-xs text-foreground/60 mt-1">
          Configure multi-tenant isolation boundaries, role-based access control, and platform infrastructure.
        </p>
      </div>

      {/* Add Member Modal */}
      {addMemberOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-2xl border border-outline-variant/30 p-6 w-full max-w-md shadow-elevation-2 space-y-4">
            <h2 className="text-base font-semibold text-foreground">Invite Member to Workspace</h2>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-1">User Email Address *</label>
                <input
                  type="email"
                  value={memberEmail}
                  onChange={(e) => setMemberEmail(e.target.value)}
                  placeholder="colleague@enterprise.com"
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Role & Permissions *</label>
                <select
                  value={memberRole}
                  onChange={(e) => setMemberRole(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                >
                  <option value="DATA_SCIENTIST">Data Scientist (Datasets & Experiments)</option>
                  <option value="ML_ENGINEER">ML Engineer (Models & Deployments)</option>
                  <option value="ADMIN">Admin (Full Workspace Management)</option>
                  <option value="VIEWER">Viewer (Read-Only Access)</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setAddMemberOpen(false)}
                className="px-4 py-2 rounded-full border border-outline-variant/40 text-xs text-foreground"
              >
                Cancel
              </button>
              <button
                disabled={addMemberMutation.isPending || !memberEmail}
                onClick={() => addMemberMutation.mutate()}
                className="px-5 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {addMemberMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Add Member
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Workspace Information */}
      <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-4">
        <h2 className="text-sm font-semibold text-foreground">Workspace Profile</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-xl bg-surface-container">
            <span className="text-foreground/50 block text-[11px]">Workspace Name</span>
            <span className="font-semibold text-foreground text-sm mt-0.5 block">
              {workspaceDetail?.name || activeWorkspace?.name || "Loading..."}
            </span>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-container">
            <span className="text-foreground/50 block text-[11px]">Tenant Slug Identifier</span>
            <span className="font-mono text-foreground text-xs mt-0.5 block">
              {workspaceDetail?.slug || activeWorkspace?.slug || "-"}
            </span>
          </div>
        </div>
      </div>

      {/* Team Members & RBAC */}
      <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-semibold text-foreground">Workspace Members & Roles</h2>
            <p className="text-xs text-foreground/50">Manage authorized users and permissions.</p>
          </div>
          <button
            onClick={() => setAddMemberOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition shadow-xs"
          >
            <UserPlus className="h-3.5 w-3.5" />
            Add Member
          </button>
        </div>

        <div className="divide-y divide-outline-variant/20 border border-outline-variant/20 rounded-xl overflow-hidden">
          {workspaceDetail?.members?.map((m: any) => (
            <div key={m.user_id} className="p-3.5 flex items-center justify-between text-xs bg-surface hover:bg-surface-container/30">
              <div>
                <span className="font-medium text-foreground block">{m.full_name}</span>
                <span className="text-[11px] text-foreground/50">{m.email}</span>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-secondary-container text-secondary-onContainer">
                {m.role}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Infrastructure & Storage Health */}
      <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-4">
        <h2 className="text-sm font-semibold text-foreground">Infrastructure Services Status</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          <div className="p-3.5 rounded-xl bg-surface-container flex items-center gap-3">
            <Database className="h-4 w-4 text-emerald-600" />
            <div>
              <span className="font-medium text-foreground block">Relational DB</span>
              <span className="text-[10px] text-emerald-600 font-semibold">PostgreSQL / SQLite Active</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-container flex items-center gap-3">
            <HardDrive className="h-4 w-4 text-primary" />
            <div>
              <span className="font-medium text-foreground block">Storage Provider</span>
              <span className="text-[10px] text-primary font-semibold">Local Storage / S3 Ready</span>
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-surface-container flex items-center gap-3">
            <Shield className="h-4 w-4 text-purple-600" />
            <div>
              <span className="font-medium text-foreground block">Authentication</span>
              <span className="text-[10px] text-purple-600 font-semibold">Argon2id + JWT Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Theme Selection */}
      <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-sm font-semibold text-foreground">Theme Preference</h2>
          <p className="text-xs text-foreground/50">Google Material 3 Light (default) or Dark Theme.</p>
        </div>
        <button
          onClick={toggleTheme}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-outline-variant/40 text-xs font-medium text-foreground hover:bg-surface-container transition"
        >
          {theme === "light" ? <Moon className="h-4 w-4 text-slate-700" /> : <Sun className="h-4 w-4 text-amber-500" />}
          Switch to {theme === "light" ? "Dark" : "Light"} Mode
        </button>
      </div>
    </div>
  );
}
