"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FlaskConical,
  Play,
  CheckCircle2,
  XCircle,
  Loader2,
  Terminal,
  BarChart2,
  Boxes,
  Clock,
  Sparkles,
} from "lucide-react";
import { api } from "@/services/api";

export default function ExperimentsPage() {
  const queryClient = useQueryClient();
  const [selectedExpId, setSelectedExpId] = useState<string | null>(null);
  const [launchOpen, setLaunchOpen] = useState(false);
  const [expName, setExpName] = useState("");
  const [datasetVersionId, setDatasetVersionId] = useState("");
  const [algorithm, setAlgorithm] = useState("logistic_regression");
  const [randomSeed, setRandomSeed] = useState(42);
  const [regModelOpen, setRegModelOpen] = useState(false);
  const [modelRegName, setModelRegName] = useState("");

  // Queries
  const { data: experiments, isLoading } = useQuery({
    queryKey: ["experiments"],
    queryFn: () => api.getExperiments(),
    refetchInterval: 3000, // Poll active status
  });

  const { data: datasets } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.getDatasets(),
  });

  const { data: selectedExp } = useQuery({
    queryKey: ["experiment", selectedExpId],
    queryFn: () => (selectedExpId ? api.getExperiment(selectedExpId) : null),
    enabled: !!selectedExpId,
    refetchInterval: (query) => (query.state.data?.status === "RUNNING" || query.state.data?.status === "QUEUED" ? 2000 : false),
  });

  // Launch Mutation
  const launchMutation = useMutation({
    mutationFn: () =>
      api.createExperiment({
        name: expName,
        dataset_version_id: datasetVersionId,
        algorithm,
        random_seed: Number(randomSeed),
      }),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["experiments"] });
      setLaunchOpen(false);
      setSelectedExpId(data.id);
    },
  });

  // Register Model Mutation
  const registerMutation = useMutation({
    mutationFn: () =>
      api.registerModel({
        name: modelRegName,
        experiment_id: selectedExpId,
        description: `Registered from experiment ${selectedExp?.name}`,
      }),
    onSuccess: () => {
      setRegModelOpen(false);
      queryClient.invalidateQueries({ queryKey: ["models"] });
      alert("Model version successfully registered in Model Registry!");
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Model Training & Experiments</h1>
          <p className="text-xs text-foreground/60 mt-1">
            Execute reproducible training pipelines, inspect live worker execution logs, and evaluate models.
          </p>
        </div>
        <button
          onClick={() => {
            if (datasets && datasets.length > 0) {
              setDatasetVersionId(datasets[0].id);
            }
            setLaunchOpen(true);
          }}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition shadow-xs"
        >
          <Play className="h-3.5 w-3.5" />
          New Training Experiment
        </button>
      </div>

      {/* Launch Experiment Modal */}
      {launchOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-2xl border border-outline-variant/30 p-6 w-full max-w-lg shadow-elevation-2 space-y-4">
            <h2 className="text-base font-semibold text-foreground">Launch ML Training Experiment</h2>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-1">Experiment Name *</label>
                <input
                  type="text"
                  value={expName}
                  onChange={(e) => setExpName(e.target.value)}
                  placeholder="e.g., Random Forest Hyperopt Run 1"
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Dataset *</label>
                <select
                  value={datasetVersionId}
                  onChange={(e) => setDatasetVersionId(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                >
                  <option value="">Select a validated dataset</option>
                  {datasets?.map((ds: any) => (
                    <option key={ds.id} value={ds.id}>
                      {ds.name} (v{ds.latest_version ?? 1} • {ds.total_rows} rows)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Algorithm *</label>
                <select
                  value={algorithm}
                  onChange={(e) => setAlgorithm(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                >
                  <option value="logistic_regression">Logistic Regression (Baseline)</option>
                  <option value="random_forest">Random Forest Classifier (Ensemble)</option>
                  <option value="hist_gradient_boosting">HistGradientBoosting (Fast GBDT)</option>
                </select>
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Random Seed</label>
                <input
                  type="number"
                  value={randomSeed}
                  onChange={(e) => setRandomSeed(Number(e.target.value))}
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setLaunchOpen(false)}
                className="px-4 py-2 rounded-full border border-outline-variant/40 text-xs font-medium text-foreground hover:bg-surface-container transition"
              >
                Cancel
              </button>
              <button
                disabled={launchMutation.isPending || !expName}
                onClick={() => launchMutation.mutate()}
                className="px-5 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition disabled:opacity-50 inline-flex items-center gap-2"
              >
                {launchMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Submit Run
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Register Model Modal */}
      {regModelOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-2xl border border-outline-variant/30 p-6 w-full max-w-md shadow-elevation-2 space-y-4">
            <h2 className="text-base font-semibold text-foreground">Register Model in Registry</h2>
            <div className="text-xs space-y-2">
              <label className="font-medium text-foreground block">Model Name *</label>
              <input
                type="text"
                value={modelRegName}
                onChange={(e) => setModelRegName(e.target.value)}
                placeholder="e.g., Telco Customer Churn Classifier"
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setRegModelOpen(false)}
                className="px-4 py-2 rounded-full border border-outline-variant/40 text-xs text-foreground"
              >
                Cancel
              </button>
              <button
                disabled={registerMutation.isPending || !modelRegName}
                onClick={() => registerMutation.mutate()}
                className="px-5 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90"
              >
                Register
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Experiments Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Experiments List */}
        <div className="lg:col-span-1 rounded-2xl border border-outline-variant/30 bg-surface p-4 shadow-xs">
          <span className="text-xs font-semibold text-foreground/70 uppercase tracking-wider block mb-3 px-2">
            Experiments ({experiments?.length ?? 0})
          </span>

          {isLoading ? (
            <div className="py-8 text-center text-xs text-foreground/50">Loading runs...</div>
          ) : experiments && experiments.length > 0 ? (
            <div className="space-y-1.5">
              {experiments.map((e: any) => {
                const isSelected = selectedExpId === e.id || (!selectedExpId && experiments[0].id === e.id);
                return (
                  <button
                    key={e.id}
                    onClick={() => setSelectedExpId(e.id)}
                    className={`w-full text-left p-3 rounded-xl transition text-xs flex flex-col gap-1 border ${
                      isSelected
                        ? "bg-primary-container/30 border-primary/40 text-foreground"
                        : "bg-surface hover:bg-surface-container border-transparent text-foreground/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground truncate">{e.name}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          e.status === "COMPLETED"
                            ? "bg-emerald-100 text-emerald-800"
                            : e.status === "RUNNING"
                            ? "bg-blue-100 text-blue-800 animate-pulse"
                            : e.status === "FAILED"
                            ? "bg-rose-100 text-rose-800"
                            : "bg-gray-100 text-gray-800"
                        }`}
                      >
                        {e.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-foreground/50">
                      <span>{e.algorithm}</span>
                      {e.accuracy && <span>Acc: {(e.accuracy * 100).toFixed(1)}%</span>}
                      {e.duration_seconds && <span>{e.duration_seconds}s</span>}
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-foreground/50">
              No training runs executed. Click New Training Experiment.
            </div>
          )}
        </div>

        {/* Right Column: Run Details, Live Logs, Metrics */}
        <div className="lg:col-span-2 space-y-6">
          {selectedExp ? (
            <>
              {/* Header Card */}
              <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-lg font-bold text-foreground">{selectedExp.name}</h2>
                  <div className="flex items-center gap-2 mt-1 text-xs text-foreground/60">
                    <span>Algorithm: <strong className="text-foreground">{selectedExp.algorithm}</strong></span>
                    <span>•</span>
                    <span>Seed: {selectedExp.random_seed}</span>
                    <span>•</span>
                    <span className="capitalize">{selectedExp.status}</span>
                  </div>
                </div>

                {selectedExp.status === "COMPLETED" && (
                  <button
                    onClick={() => {
                      setModelRegName(selectedExp.name);
                      setRegModelOpen(true);
                    }}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition shadow-xs self-start"
                  >
                    <Boxes className="h-3.5 w-3.5" />
                    Register in Model Registry
                  </button>
                )}
              </div>

              {/* Metrics Card (if completed) */}
              {selectedExp.metrics && (
                <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-5">
                  <div className="flex items-center gap-2 text-xs font-semibold text-foreground/80 uppercase tracking-wider">
                    <BarChart2 className="h-4 w-4 text-primary" />
                    Evaluation Metrics (Untouched Test Split)
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
                    <div className="p-3 rounded-xl bg-surface-container">
                      <span className="text-[11px] text-foreground/60 block">Accuracy</span>
                      <span className="text-xl font-bold text-foreground mt-0.5 block">
                        {(selectedExp.metrics.accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-surface-container">
                      <span className="text-[11px] text-foreground/60 block">Precision</span>
                      <span className="text-xl font-bold text-foreground mt-0.5 block">
                        {(selectedExp.metrics.precision * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-surface-container">
                      <span className="text-[11px] text-foreground/60 block">Recall</span>
                      <span className="text-xl font-bold text-foreground mt-0.5 block">
                        {(selectedExp.metrics.recall * 100).toFixed(1)}%
                      </span>
                    </div>
                    <div className="p-3 rounded-xl bg-surface-container">
                      <span className="text-[11px] text-foreground/60 block">F1 Score</span>
                      <span className="text-xl font-bold text-foreground mt-0.5 block">
                        {(selectedExp.metrics.f1_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {/* Confusion Matrix */}
                  {selectedExp.metrics.confusion_matrix && (
                    <div className="pt-2">
                      <span className="text-xs font-medium text-foreground block mb-2">Confusion Matrix</span>
                      <div className="grid grid-cols-2 max-w-xs gap-1.5 text-xs text-center font-mono">
                        <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200">
                          <span className="text-[10px] text-emerald-700 block">TN (True Neg)</span>
                          <strong className="text-sm">{selectedExp.metrics.confusion_matrix[0][0]}</strong>
                        </div>
                        <div className="p-2.5 rounded-lg bg-rose-50 text-rose-900 border border-rose-200">
                          <span className="text-[10px] text-rose-700 block">FP (False Pos)</span>
                          <strong className="text-sm">{selectedExp.metrics.confusion_matrix[0][1]}</strong>
                        </div>
                        <div className="p-2.5 rounded-lg bg-rose-50 text-rose-900 border border-rose-200">
                          <span className="text-[10px] text-rose-700 block">FN (False Neg)</span>
                          <strong className="text-sm">{selectedExp.metrics.confusion_matrix[1][0]}</strong>
                        </div>
                        <div className="p-2.5 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200">
                          <span className="text-[10px] text-emerald-700 block">TP (True Pos)</span>
                          <strong className="text-sm">{selectedExp.metrics.confusion_matrix[1][1]}</strong>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Live Worker Logs Console */}
              <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-semibold text-foreground/80 uppercase tracking-wider">
                    <Terminal className="h-4 w-4 text-primary" />
                    Training Logs & Execution Stream
                  </div>
                  {selectedExp.status === "RUNNING" && (
                    <span className="inline-flex items-center gap-1.5 text-xs text-blue-600 font-medium">
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      Running...
                    </span>
                  )}
                </div>

                <pre className="p-4 rounded-xl bg-slate-950 text-slate-200 font-mono text-xs overflow-x-auto max-h-80 leading-relaxed">
                  {selectedExp.logs || "No logs received from task worker."}
                </pre>
              </div>
            </>
          ) : (
            <div className="py-16 text-center text-xs text-foreground/40 bg-surface rounded-2xl border border-outline-variant/30">
              Select an experiment from the left column to view live logs and evaluation metrics.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
