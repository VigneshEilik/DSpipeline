"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Rocket,
  CheckCircle2,
  AlertCircle,
  RotateCcw,
  Copy,
  ExternalLink,
  Plus,
  Loader2,
} from "lucide-react";
import { api } from "@/services/api";

export default function DeploymentsPage() {
  const queryClient = useQueryClient();
  const [deployOpen, setDeployOpen] = useState(false);
  const [rollbackOpen, setRollbackOpen] = useState(false);
  const [activeDepId, setActiveDepId] = useState<string | null>(null);
  const [deployName, setDeployName] = useState("");
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [rollbackTargetId, setRollbackTargetId] = useState("");
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const { data: deployments, isLoading } = useQuery({
    queryKey: ["deployments"],
    queryFn: () => api.getDeployments(),
  });

  const { data: models } = useQuery({
    queryKey: ["models"],
    queryFn: () => api.getModels(),
  });

  // Extract all approved versions
  const approvedVersions: any[] = [];
  models?.forEach((m: any) => {
    m.versions?.forEach((v: any) => {
      if (v.lifecycle_stage === "APPROVED" || v.lifecycle_stage === "DEPLOYED") {
        approvedVersions.push({
          ...v,
          modelName: m.name,
        });
      }
    });
  });

  // Deploy Mutation
  const deployMutation = useMutation({
    mutationFn: () =>
      api.createDeployment({
        name: deployName,
        model_version_id: selectedVersionId,
        environment: "production",
        traffic_percentage: 100,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] });
      setDeployOpen(false);
      setDeployName("");
      setSelectedVersionId("");
    },
  });

  // Rollback Mutation
  const rollbackMutation = useMutation({
    mutationFn: () =>
      api.rollbackDeployment(activeDepId!, {
        target_model_version_id: rollbackTargetId,
        reason: "User requested manual operational rollback",
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["deployments"] });
      setRollbackOpen(false);
    },
  });

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Model Deployments & Serving</h1>
          <p className="text-xs text-foreground/60 mt-1">
            Manage live inference endpoints, traffic routing, and atomic rollback workflows.
          </p>
        </div>
        <button
          onClick={() => setDeployOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition shadow-xs"
        >
          <Plus className="h-3.5 w-3.5" />
          Deploy Approved Model
        </button>
      </div>

      {/* Deploy Modal */}
      {deployOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-2xl border border-outline-variant/30 p-6 w-full max-w-md shadow-elevation-2 space-y-4">
            <h2 className="text-base font-semibold text-foreground">Deploy Approved Model Version</h2>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-1">Deployment Name *</label>
                <input
                  type="text"
                  value={deployName}
                  onChange={(e) => setDeployName(e.target.value)}
                  placeholder="e.g., Churn Predictor Prod Endpoint"
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Approved Model Version *</label>
                <select
                  value={selectedVersionId}
                  onChange={(e) => setSelectedVersionId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                >
                  <option value="">Select an approved version</option>
                  {approvedVersions.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.modelName} (v{v.version_number} • {v.algorithm})
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setDeployOpen(false)}
                className="px-4 py-2 rounded-full border border-outline-variant/40 text-xs text-foreground"
              >
                Cancel
              </button>
              <button
                disabled={deployMutation.isPending || !deployName || !selectedVersionId}
                onClick={() => deployMutation.mutate()}
                className="px-5 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {deployMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Activate Endpoint
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Rollback Modal */}
      {rollbackOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-2xl border border-outline-variant/30 p-6 w-full max-w-md shadow-elevation-2 space-y-4">
            <h2 className="text-base font-semibold text-foreground">Confirm Rollback</h2>
            <p className="text-xs text-foreground/70 leading-relaxed">
              This will atomically switch traffic to a previously approved model version without downtime.
            </p>

            <div className="text-xs space-y-2">
              <label className="font-medium text-foreground block">Select Target Version *</label>
              <select
                value={rollbackTargetId}
                onChange={(e) => setRollbackTargetId(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              >
                <option value="">Select rollback version</option>
                {approvedVersions.map((v) => (
                  <option key={v.id} value={v.id}>
                    {v.modelName} v{v.version_number} ({v.algorithm})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setRollbackOpen(false)}
                className="px-4 py-2 rounded-full border border-outline-variant/40 text-xs text-foreground"
              >
                Cancel
              </button>
              <button
                disabled={rollbackMutation.isPending || !rollbackTargetId}
                onClick={() => rollbackMutation.mutate()}
                className="px-5 py-2 rounded-full bg-rose-600 text-white text-xs font-medium hover:opacity-90 disabled:opacity-50"
              >
                Confirm Rollback
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Deployments List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-foreground/50">Loading deployments...</div>
        ) : deployments && deployments.length > 0 ? (
          <div className="grid grid-cols-1 gap-4">
            {deployments.map((d: any) => {
              const isActive = d.status === "ACTIVE";
              return (
                <div
                  key={d.id}
                  className="p-6 rounded-2xl border border-outline-variant/30 bg-surface shadow-xs space-y-4"
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2.5 rounded-xl bg-primary-container text-primary-onContainer">
                        <Rocket className="h-5 w-5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <h2 className="text-base font-bold text-foreground">{d.name}</h2>
                          <span
                            className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                              isActive ? "bg-emerald-100 text-emerald-800" : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {d.status}
                          </span>
                        </div>
                        <span className="text-xs text-foreground/50">
                          Environment: <strong className="text-foreground/80">{d.environment}</strong> • Algorithm: {d.algorithm}
                        </span>
                      </div>
                    </div>

                    {isActive && (
                      <button
                        onClick={() => {
                          setActiveDepId(d.id);
                          setRollbackOpen(true);
                        }}
                        className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border border-outline-variant/40 text-xs font-medium text-foreground hover:bg-surface-container transition self-start"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        Rollback
                      </button>
                    )}
                  </div>

                  {/* Endpoint URI & Traffic */}
                  <div className="p-3.5 rounded-xl bg-surface-container flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
                    <div className="flex items-center gap-2 overflow-hidden">
                      <span className="text-foreground/50 font-medium">Endpoint:</span>
                      <code className="text-foreground font-mono text-[11px] truncate">{d.endpoint_url}</code>
                    </div>

                    <button
                      onClick={() => copyToClipboard(`http://localhost:8000${d.endpoint_url}`, d.id)}
                      className="inline-flex items-center gap-1 text-[11px] text-primary hover:underline shrink-0"
                    >
                      <Copy className="h-3.5 w-3.5" />
                      {copiedId === d.id ? "Copied!" : "Copy Full URL"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="py-16 text-center text-xs text-foreground/40 bg-surface rounded-2xl border border-outline-variant/30">
            No active deployments. Deploy an approved model version to begin serving inference.
          </div>
        )}
      </div>
    </div>
  );
}
