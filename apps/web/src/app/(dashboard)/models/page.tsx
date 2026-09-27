"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Boxes,
  ShieldCheck,
  CheckCircle,
  XCircle,
  Rocket,
  Clock,
  ChevronRight,
  GitBranch,
  Loader2,
} from "lucide-react";
import { api } from "@/services/api";

export default function ModelRegistryPage() {
  const queryClient = useQueryClient();
  const [selectedModelId, setSelectedModelId] = useState<string | null>(null);
  const [approveOpen, setApproveOpen] = useState(false);
  const [selectedVersionId, setSelectedVersionId] = useState<string | null>(null);
  const [decision, setDecision] = useState<"APPROVED" | "REJECTED">("APPROVED");
  const [comments, setComments] = useState("");

  const { data: models, isLoading } = useQuery({
    queryKey: ["models"],
    queryFn: () => api.getModels(),
  });

  const { data: selectedModel } = useQuery({
    queryKey: ["model", selectedModelId],
    queryFn: () => (selectedModelId ? api.getModel(selectedModelId) : null),
    enabled: !!selectedModelId,
  });

  const approveMutation = useMutation({
    mutationFn: () =>
      api.approveModel(selectedModelId!, {
        version_id: selectedVersionId,
        decision,
        comments,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      queryClient.invalidateQueries({ queryKey: ["model", selectedModelId] });
      setApproveOpen(false);
      setComments("");
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Model Registry & Governance</h1>
        <p className="text-xs text-foreground/60 mt-1">
          Review version lineage, audit approval gates, and promote candidate models to production serving.
        </p>
      </div>

      {/* Approval Modal */}
      {approveOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-2xl border border-outline-variant/30 p-6 w-full max-w-md shadow-elevation-2 space-y-4">
            <h2 className="text-base font-semibold text-foreground">Governance Decision Gate</h2>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-2">Review Decision *</label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      checked={decision === "APPROVED"}
                      onChange={() => setDecision("APPROVED")}
                      className="text-primary"
                    />
                    <span className="text-emerald-700 font-semibold">Approve for Deployment</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="decision"
                      checked={decision === "REJECTED"}
                      onChange={() => setDecision("REJECTED")}
                      className="text-rose-600"
                    />
                    <span className="text-rose-700 font-semibold">Reject</span>
                  </label>
                </div>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Audit Comments / Evaluation Review *</label>
                <textarea
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  placeholder="e.g., Performance meets threshold; zero data leakage verified."
                  rows={3}
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setApproveOpen(false)}
                className="px-4 py-2 rounded-full border border-outline-variant/40 text-xs text-foreground hover:bg-surface-container"
              >
                Cancel
              </button>
              <button
                disabled={approveMutation.isPending || !comments}
                onClick={() => approveMutation.mutate()}
                className="px-5 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 disabled:opacity-50 inline-flex items-center gap-2"
              >
                {approveMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Submit Decision
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Models List */}
        <div className="lg:col-span-1 rounded-2xl border border-outline-variant/30 bg-surface p-4 shadow-xs">
          <span className="text-xs font-semibold text-foreground/70 uppercase tracking-wider block mb-3 px-2">
            Registered Models ({models?.length ?? 0})
          </span>

          {isLoading ? (
            <div className="py-8 text-center text-xs text-foreground/50">Loading registry...</div>
          ) : models && models.length > 0 ? (
            <div className="space-y-1.5">
              {models.map((m: any) => {
                const isSelected = selectedModelId === m.id || (!selectedModelId && models[0].id === m.id);
                return (
                  <button
                    key={m.id}
                    onClick={() => setSelectedModelId(m.id)}
                    className={`w-full text-left p-3 rounded-xl transition text-xs flex flex-col gap-1 border ${
                      isSelected
                        ? "bg-primary-container/30 border-primary/40 text-foreground"
                        : "bg-surface hover:bg-surface-container border-transparent text-foreground/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground truncate">{m.name}</span>
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-secondary-container text-secondary-onContainer font-semibold">
                        v{m.latest_version?.version_number ?? 1}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-foreground/50">
                      <span>{m.task_type}</span>
                      <span>•</span>
                      <span>{m.versions?.length ?? 0} version(s)</span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-foreground/50">
              No models in registry. Train and register an experiment run.
            </div>
          )}
        </div>

        {/* Model Versions & Governance Timeline */}
        <div className="lg:col-span-2 space-y-6">
          {selectedModel ? (
            <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-6">
              <div>
                <h2 className="text-lg font-bold text-foreground">{selectedModel.name}</h2>
                <p className="text-xs text-foreground/60">{selectedModel.description || "Production model registry entry."}</p>
              </div>

              {/* Version History Table */}
              <div className="space-y-3">
                <span className="text-xs font-semibold text-foreground/70 uppercase tracking-wider block">
                  Version History & Lifecycle Gates
                </span>

                <div className="space-y-3">
                  {selectedModel.versions?.map((v: any) => {
                    const isApproved = v.lifecycle_stage === "APPROVED";
                    const isDeployed = v.lifecycle_stage === "DEPLOYED";

                    return (
                      <div
                        key={v.id}
                        className="p-4 rounded-xl border border-outline-variant/25 bg-surface-container/50 space-y-3"
                      >
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-sm text-foreground">Version {v.version_number}</span>
                            <span className="text-xs text-foreground/50">({v.algorithm})</span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                                isDeployed
                                  ? "bg-purple-100 text-purple-800"
                                  : isApproved
                                  ? "bg-emerald-100 text-emerald-800"
                                  : v.lifecycle_stage === "REJECTED"
                                  ? "bg-rose-100 text-rose-800"
                                  : "bg-blue-100 text-blue-800"
                              }`}
                            >
                              {v.lifecycle_stage}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            {/* Action: Approve / Reject */}
                            {!isApproved && !isDeployed && (
                              <button
                                onClick={() => {
                                  setSelectedVersionId(v.id);
                                  setApproveOpen(true);
                                }}
                                className="px-3 py-1.5 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition shadow-xs"
                              >
                                Governance Review
                              </button>
                            )}

                            {/* Action: Deploy (if approved) */}
                            {isApproved && (
                              <Link
                                href={`/deployments?model_version_id=${v.id}`}
                                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-600 text-white text-xs font-medium hover:opacity-90 transition shadow-xs"
                              >
                                <Rocket className="h-3.5 w-3.5" />
                                Deploy to Production
                              </Link>
                            )}
                          </div>
                        </div>

                        {/* Artifact & Lineage Details */}
                        <div className="text-[11px] text-foreground/60 space-y-1">
                          <div>Artifact URI: <code className="text-foreground/80 font-mono">{v.artifact_uri}</code></div>
                          {v.approvals?.length > 0 && (
                            <div className="mt-2 pt-2 border-t border-outline-variant/20 space-y-1">
                              <span className="font-semibold text-foreground/80 block">Approval Audit:</span>
                              {v.approvals.map((a: any) => (
                                <div key={a.id} className="text-foreground/70 italic">
                                  "{a.comments}" • Decision: <strong className="text-foreground">{a.decision}</strong>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-xs text-foreground/40 bg-surface rounded-2xl border border-outline-variant/30">
              Select a model to review version history and approval gates.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
