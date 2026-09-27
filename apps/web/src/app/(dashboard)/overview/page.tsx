"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import {
  Activity,
  Boxes,
  Database,
  FlaskConical,
  Rocket,
  Sparkles,
  ArrowUpRight,
  Clock,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";
import { api } from "@/services/api";

export default function OverviewPage() {
  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["monitoring-overview"],
    queryFn: () => api.getMonitoringOverview(),
  });

  const { data: deployments } = useQuery({
    queryKey: ["deployments"],
    queryFn: () => api.getDeployments(),
  });

  const { data: experiments } = useQuery({
    queryKey: ["experiments"],
    queryFn: () => api.getExperiments(),
  });

  return (
    <div className="space-y-8">
      {/* Title Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Platform Overview
        </h1>
        <p className="text-xs text-foreground/60 mt-1">
          Operational telemetry and model lifecycle metrics for the current workspace.
        </p>
      </div>

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Datasets */}
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-foreground/60">Validated Datasets</span>
            <Database className="h-4 w-4 text-primary" />
          </div>
          <div className="mt-3 text-2xl font-bold text-foreground">
            {overview?.datasets_count ?? 0}
          </div>
          <Link href="/datasets" className="mt-2 inline-flex items-center gap-1 text-[11px] text-primary hover:underline">
            Manage datasets <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Experiments */}
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-foreground/60">Training Runs</span>
            <FlaskConical className="h-4 w-4 text-secondary" />
          </div>
          <div className="mt-3 text-2xl font-bold text-foreground">
            {overview?.experiments_count ?? 0}
          </div>
          <Link href="/experiments" className="mt-2 inline-flex items-center gap-1 text-[11px] text-secondary hover:underline">
            View runs <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Registered Models */}
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-foreground/60">Registered Models</span>
            <Boxes className="h-4 w-4 text-tertiary" />
          </div>
          <div className="mt-3 text-2xl font-bold text-foreground">
            {overview?.registered_models_count ?? 0}
          </div>
          <Link href="/models" className="mt-2 inline-flex items-center gap-1 text-[11px] text-tertiary hover:underline">
            Model registry <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>

        {/* Active Deployments */}
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-foreground/60">Active Endpoints</span>
            <Rocket className="h-4 w-4 text-emerald-600" />
          </div>
          <div className="mt-3 text-2xl font-bold text-foreground">
            {overview?.active_deployments_count ?? 0}
          </div>
          <Link href="/deployments" className="mt-2 inline-flex items-center gap-1 text-[11px] text-emerald-600 hover:underline">
            Serving status <ArrowUpRight className="h-3 w-3" />
          </Link>
        </div>
      </div>

      {/* Serving Telemetry & Risk Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Latency Metrics */}
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs">
          <div className="flex items-center gap-2 text-xs font-semibold text-foreground/80 uppercase tracking-wider mb-4">
            <Clock className="h-4 w-4 text-primary" />
            Serving Latency
          </div>
          <div className="space-y-4">
            <div className="flex justify-between items-center text-xs">
              <span className="text-foreground/70">Average Latency</span>
              <span className="font-semibold text-foreground">{overview?.average_latency_ms ?? 0} ms</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-foreground/70">p50 Percentile</span>
              <span className="font-semibold text-foreground">{overview?.p50_latency_ms ?? 0} ms</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-foreground/70">p95 Percentile</span>
              <span className="font-semibold text-foreground">{overview?.p95_latency_ms ?? 0} ms</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-foreground/70">p99 Percentile</span>
              <span className="font-semibold text-foreground">{overview?.p99_latency_ms ?? 0} ms</span>
            </div>
          </div>
        </div>

        {/* Prediction Volume & Risk Distribution */}
        <div className="md:col-span-2 rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2 text-xs font-semibold text-foreground/80 uppercase tracking-wider">
              <Sparkles className="h-4 w-4 text-secondary" />
              Inference Volume & Customer Churn Risk
            </div>
            <span className="text-xs text-foreground/60">
              Total Invocations: <strong className="text-foreground">{overview?.total_predictions ?? 0}</strong>
            </span>
          </div>

          <div className="grid grid-cols-3 gap-4 mt-6">
            <div className="p-4 rounded-xl bg-surface-container text-center">
              <span className="text-[11px] font-medium text-emerald-600 block">Low Risk</span>
              <span className="text-2xl font-bold text-foreground mt-1 block">
                {overview?.risk_distribution?.low ?? 0}
              </span>
              <span className="text-[10px] text-foreground/50">Prob &lt; 35%</span>
            </div>
            <div className="p-4 rounded-xl bg-surface-container text-center">
              <span className="text-[11px] font-medium text-amber-600 block">Medium Risk</span>
              <span className="text-2xl font-bold text-foreground mt-1 block">
                {overview?.risk_distribution?.medium ?? 0}
              </span>
              <span className="text-[10px] text-foreground/50">35% - 65%</span>
            </div>
            <div className="p-4 rounded-xl bg-surface-container text-center">
              <span className="text-[11px] font-medium text-rose-600 block">High Risk</span>
              <span className="text-2xl font-bold text-foreground mt-1 block">
                {overview?.risk_distribution?.high ?? 0}
              </span>
              <span className="text-[10px] text-foreground/50">Prob &ge; 65%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Experiments & Active Serving Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Recent Training Runs */}
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Recent Experiments</h2>
            <Link href="/experiments" className="text-xs text-primary hover:underline">
              View all
            </Link>
          </div>
          {experiments && experiments.length > 0 ? (
            <div className="divide-y divide-outline-variant/20">
              {experiments.slice(0, 4).map((exp: any) => (
                <div key={exp.id} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-medium text-foreground block">{exp.name}</span>
                    <span className="text-[11px] text-foreground/50">{exp.algorithm}</span>
                  </div>
                  <div className="text-right">
                    <span
                      className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                        exp.status === "COMPLETED"
                          ? "bg-emerald-100 text-emerald-800"
                          : exp.status === "RUNNING"
                          ? "bg-blue-100 text-blue-800 animate-pulse"
                          : "bg-gray-100 text-gray-800"
                      }`}
                    >
                      {exp.status}
                    </span>
                    {exp.accuracy && (
                      <span className="text-[10px] text-foreground/60 block mt-0.5">
                        Acc: {(exp.accuracy * 100).toFixed(1)}%
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-foreground/50">
              No training runs yet. Launch your first experiment in the Experiments tab.
            </div>
          )}
        </div>

        {/* Active Deployments */}
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-semibold text-foreground">Active Deployments</h2>
            <Link href="/deployments" className="text-xs text-primary hover:underline">
              Manage
            </Link>
          </div>
          {deployments && deployments.length > 0 ? (
            <div className="divide-y divide-outline-variant/20">
              {deployments.slice(0, 4).map((dep: any) => (
                <div key={dep.id} className="py-2.5 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-medium text-foreground block">{dep.name}</span>
                    <span className="text-[11px] text-foreground/50">{dep.endpoint_url}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                    {dep.status}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-foreground/50">
              No active deployments. Register and approve a model to deploy.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
