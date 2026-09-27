"use client";

import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Play,
  TrendingDown,
  TrendingUp,
  BarChart,
  Loader2,
} from "lucide-react";
import { api } from "@/services/api";

export default function MonitoringPage() {
  const queryClient = useQueryClient();

  const { data: overview, isLoading: loadingOverview } = useQuery({
    queryKey: ["monitoring-overview"],
    queryFn: () => api.getMonitoringOverview(),
    refetchInterval: 5000,
  });

  const { data: drift, isLoading: loadingDrift } = useQuery({
    queryKey: ["monitoring-drift"],
    queryFn: () => api.getLatestDrift(),
  });

  const runDriftMutation = useMutation({
    mutationFn: () => api.runDrift({ sample_size: 100 }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["monitoring-drift"] });
    },
  });

  return (
    <div className="space-y-8">
      {/* Header & Run Drift Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Observability & Drift Monitoring</h1>
          <p className="text-xs text-foreground/60 mt-1">
            Track serving latency percentiles, request volume, and statistical distribution drift between reference data and live traffic.
          </p>
        </div>
        <button
          disabled={runDriftMutation.isPending}
          onClick={() => runDriftMutation.mutate()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition shadow-xs disabled:opacity-50"
        >
          {runDriftMutation.isPending ? (
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
          ) : (
            <Play className="h-3.5 w-3.5" />
          )}
          Calculate Statistical Drift
        </button>
      </div>

      {/* Service Telemetry Percentiles */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <span className="text-xs font-medium text-foreground/60 block">p50 Latency (Median)</span>
          <span className="text-2xl font-bold text-foreground mt-2 block">
            {overview?.p50_latency_ms ?? 0} ms
          </span>
          <span className="text-[11px] text-emerald-600 font-medium mt-1 block">Normal SLA</span>
        </div>

        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <span className="text-xs font-medium text-foreground/60 block">p95 Latency</span>
          <span className="text-2xl font-bold text-foreground mt-2 block">
            {overview?.p95_latency_ms ?? 0} ms
          </span>
          <span className="text-[11px] text-foreground/50 mt-1 block">95% under SLA</span>
        </div>

        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <span className="text-xs font-medium text-foreground/60 block">p99 Latency (Tail)</span>
          <span className="text-2xl font-bold text-foreground mt-2 block">
            {overview?.p99_latency_ms ?? 0} ms
          </span>
          <span className="text-[11px] text-foreground/50 mt-1 block">Tail latency</span>
        </div>

        <div className="rounded-2xl border border-outline-variant/30 bg-surface p-5 shadow-xs">
          <span className="text-xs font-medium text-foreground/60 block">Total Invocations</span>
          <span className="text-2xl font-bold text-foreground mt-2 block">
            {overview?.total_predictions ?? 0}
          </span>
          <span className="text-[11px] text-primary mt-1 block">All endpoints</span>
        </div>
      </div>

      {/* Statistical Data Drift Analysis */}
      <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <h2 className="text-base font-bold text-foreground">Kolmogorov-Smirnov Data Drift Audit</h2>
            </div>
            <p className="text-xs text-foreground/60 mt-0.5">
              Compares the baseline training feature distribution against recent production inference traffic.
            </p>
          </div>

          {drift && (
            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${
                drift.drift_detected
                  ? "bg-rose-100 text-rose-800 border border-rose-300"
                  : "bg-emerald-100 text-emerald-800 border border-emerald-300"
              }`}
            >
              {drift.drift_detected ? "Significant Drift Detected" : "No Critical Drift Detected"}
            </span>
          )}
        </div>

        {loadingDrift ? (
          <div className="py-12 text-center text-xs text-foreground/50">Analyzing feature drift...</div>
        ) : drift ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
              <div className="p-3 rounded-xl bg-surface-container">
                <span className="text-foreground/60 text-[11px] block">Drift Share</span>
                <span className="text-xl font-bold text-foreground mt-1 block">
                  {(drift.drift_share * 100).toFixed(0)}%
                </span>
                <span className="text-[10px] text-foreground/50">Threshold: 33%</span>
              </div>

              <div className="p-3 rounded-xl bg-surface-container">
                <span className="text-foreground/60 text-[11px] block">Drifted Feature Count</span>
                <span className="text-xl font-bold text-foreground mt-1 block">
                  {drift.drifted_features?.length ?? 0}
                </span>
                <span className="text-[10px] text-foreground/50">Features with p &lt; 0.05</span>
              </div>

              <div className="p-3 rounded-xl bg-surface-container">
                <span className="text-foreground/60 text-[11px] block">Audit Timestamp</span>
                <span className="text-xs font-semibold text-foreground mt-1 block">
                  {new Date(drift.created_at).toLocaleTimeString()}
                </span>
                <span className="text-[10px] text-foreground/50">Last calculation</span>
              </div>
            </div>

            {/* Feature Metrics Table */}
            <div className="overflow-x-auto border border-outline-variant/20 rounded-xl">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-container text-foreground/70 border-b border-outline-variant/20 text-[11px]">
                  <tr>
                    <th className="px-4 py-2 font-semibold">Feature</th>
                    <th className="px-4 py-2 font-semibold">Statistical Test</th>
                    <th className="px-4 py-2 font-semibold">p-value</th>
                    <th className="px-4 py-2 font-semibold">Reference Mean</th>
                    <th className="px-4 py-2 font-semibold">Inference Mean</th>
                    <th className="px-4 py-2 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-variant/10 text-foreground/80">
                  {drift.feature_metrics?.map((fm: any) => (
                    <tr key={fm.feature_name} className="hover:bg-surface-container/50">
                      <td className="px-4 py-2.5 font-medium text-foreground">{fm.feature_name}</td>
                      <td className="px-4 py-2.5 text-foreground/60">{fm.test_name}</td>
                      <td className="px-4 py-2.5 font-mono">{fm.drift_score.toFixed(4)}</td>
                      <td className="px-4 py-2.5">{fm.reference_mean ?? "-"}</td>
                      <td className="px-4 py-2.5">{fm.current_mean ?? "-"}</td>
                      <td className="px-4 py-2.5">
                        {fm.is_drifted ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-rose-100 text-rose-800">
                            Drifted
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800">
                            Stable
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="py-12 text-center text-xs text-foreground/50">
            No drift report calculated yet. Click "Calculate Statistical Drift" above.
          </div>
        )}
      </div>
    </div>
  );
}
