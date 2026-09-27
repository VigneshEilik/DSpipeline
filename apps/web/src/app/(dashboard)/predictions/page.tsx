"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Sparkles,
  Zap,
  Clock,
  History,
  AlertTriangle,
  CheckCircle2,
  FileSpreadsheet,
  Upload,
  Loader2,
  RefreshCw,
} from "lucide-react";
import { api } from "@/services/api";

const HIGH_RISK_PRESET = {
  tenure: 1,
  MonthlyCharges: 95.5,
  TotalCharges: 95.5,
  gender: "Female",
  SeniorCitizen: 0,
  Partner: "No",
  Dependents: "No",
  PhoneService: "Yes",
  MultipleLines: "No",
  InternetService: "Fiber optic",
  OnlineSecurity: "No",
  OnlineBackup: "No",
  DeviceProtection: "No",
  TechSupport: "No",
  StreamingTV: "Yes",
  StreamingMovies: "Yes",
  Contract: "Month-to-month",
  PaperlessBilling: "Yes",
  PaymentMethod: "Electronic check",
};

const LOW_RISK_PRESET = {
  tenure: 60,
  MonthlyCharges: 45.0,
  TotalCharges: 2700.0,
  gender: "Male",
  SeniorCitizen: 0,
  Partner: "Yes",
  Dependents: "Yes",
  PhoneService: "Yes",
  MultipleLines: "Yes",
  InternetService: "DSL",
  OnlineSecurity: "Yes",
  OnlineBackup: "Yes",
  DeviceProtection: "Yes",
  TechSupport: "Yes",
  StreamingTV: "No",
  StreamingMovies: "No",
  Contract: "Two year",
  PaperlessBilling: "No",
  PaymentMethod: "Bank transfer (automatic)",
};

export default function PredictionsPage() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<any>(HIGH_RISK_PRESET);
  const [predictionResult, setPredictionResult] = useState<any>(null);
  const [predictError, setPredictError] = useState<string | null>(null);

  const { data: deployments } = useQuery({
    queryKey: ["deployments"],
    queryFn: () => api.getDeployments(),
  });

  const { data: history, isLoading: loadingHistory } = useQuery({
    queryKey: ["predictions-history"],
    queryFn: () => api.getPredictions(20, 0),
    refetchInterval: 5000,
  });

  const activeDeployment = deployments?.find((d: any) => d.status === "ACTIVE");

  const predictMutation = useMutation({
    mutationFn: () => api.predictSingle(formData, activeDeployment?.id),
    onSuccess: (data) => {
      setPredictionResult(data);
      setPredictError(null);
      queryClient.invalidateQueries({ queryKey: ["predictions-history"] });
      queryClient.invalidateQueries({ queryKey: ["monitoring-overview"] });
    },
    onError: (err: any) => {
      setPredictError(err.message || "Prediction request failed.");
    },
  });

  const handleInputChange = (field: string, val: any) => {
    setFormData((prev: any) => ({ ...prev, [field]: val }));
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">Real-Time Inference & Predictions</h1>
        <p className="text-xs text-foreground/60 mt-1">
          Submit customer attributes to the active serving pipeline to estimate churn probability in real time.
        </p>
      </div>

      {/* Serving Notice */}
      {!activeDeployment && (
        <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 shrink-0 text-amber-600" />
          <span>
            No active deployment detected in this workspace. Please deploy an approved model in the Deployments tab first.
          </span>
        </div>
      )}

      {/* Inference Form & Live Result Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Form Inputs */}
        <div className="lg:col-span-2 rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-outline-variant/20">
            <span className="text-xs font-semibold text-foreground/80 uppercase tracking-wider">
              Customer Attributes & Telemetry
            </span>
            <div className="flex items-center gap-2 text-xs">
              <span className="text-foreground/50 text-[11px]">Quick Presets:</span>
              <button
                type="button"
                onClick={() => setFormData(HIGH_RISK_PRESET)}
                className="px-2.5 py-1 rounded-full bg-rose-50 text-rose-700 font-medium text-[10px] hover:bg-rose-100"
              >
                High Risk
              </button>
              <button
                type="button"
                onClick={() => setFormData(LOW_RISK_PRESET)}
                className="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 font-medium text-[10px] hover:bg-emerald-100"
              >
                Low Risk
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
            {/* Tenure */}
            <div>
              <label className="font-medium text-foreground block mb-1">Tenure (Months)</label>
              <input
                type="number"
                value={formData.tenure}
                onChange={(e) => handleInputChange("tenure", Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              />
            </div>

            {/* Monthly Charges */}
            <div>
              <label className="font-medium text-foreground block mb-1">Monthly Charges ($)</label>
              <input
                type="number"
                step="0.01"
                value={formData.MonthlyCharges}
                onChange={(e) => handleInputChange("MonthlyCharges", Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              />
            </div>

            {/* Total Charges */}
            <div>
              <label className="font-medium text-foreground block mb-1">Total Charges ($)</label>
              <input
                type="number"
                step="0.01"
                value={formData.TotalCharges}
                onChange={(e) => handleInputChange("TotalCharges", Number(e.target.value))}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              />
            </div>

            {/* Contract */}
            <div>
              <label className="font-medium text-foreground block mb-1">Contract Type</label>
              <select
                value={formData.Contract}
                onChange={(e) => handleInputChange("Contract", e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              >
                <option value="Month-to-month">Month-to-month</option>
                <option value="One year">One year</option>
                <option value="Two year">Two year</option>
              </select>
            </div>

            {/* Internet Service */}
            <div>
              <label className="font-medium text-foreground block mb-1">Internet Service</label>
              <select
                value={formData.InternetService}
                onChange={(e) => handleInputChange("InternetService", e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              >
                <option value="Fiber optic">Fiber optic</option>
                <option value="DSL">DSL</option>
                <option value="No">No</option>
              </select>
            </div>

            {/* Tech Support */}
            <div>
              <label className="font-medium text-foreground block mb-1">Tech Support</label>
              <select
                value={formData.TechSupport}
                onChange={(e) => handleInputChange("TechSupport", e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              >
                <option value="No">No</option>
                <option value="Yes">Yes</option>
                <option value="No internet service">No internet service</option>
              </select>
            </div>

            {/* Payment Method */}
            <div className="sm:col-span-2">
              <label className="font-medium text-foreground block mb-1">Payment Method</label>
              <select
                value={formData.PaymentMethod}
                onChange={(e) => handleInputChange("PaymentMethod", e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              >
                <option value="Electronic check">Electronic check</option>
                <option value="Mailed check">Mailed check</option>
                <option value="Bank transfer (automatic)">Bank transfer (automatic)</option>
                <option value="Credit card (automatic)">Credit card (automatic)</option>
              </select>
            </div>

            {/* Paperless Billing */}
            <div>
              <label className="font-medium text-foreground block mb-1">Paperless Billing</label>
              <select
                value={formData.PaperlessBilling}
                onChange={(e) => handleInputChange("PaperlessBilling", e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
              >
                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </div>
          </div>

          {predictError && (
            <div className="p-3 rounded-xl bg-error-container text-error-onContainer text-xs">
              {predictError}
            </div>
          )}

          <div className="flex justify-end pt-2">
            <button
              disabled={predictMutation.isPending || !activeDeployment}
              onClick={() => predictMutation.mutate()}
              className="px-6 py-2.5 rounded-full bg-primary text-primary-foreground text-xs font-semibold hover:opacity-90 disabled:opacity-50 transition shadow-xs inline-flex items-center gap-2"
            >
              {predictMutation.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
              Evaluate Churn Probability
            </button>
          </div>
        </div>

        {/* Prediction Output Gauge */}
        <div className="lg:col-span-1 rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs flex flex-col justify-between">
          <span className="text-xs font-semibold text-foreground/80 uppercase tracking-wider block mb-4">
            Inference Response
          </span>

          {predictionResult ? (
            <div className="space-y-6 text-center my-auto">
              <div>
                <span className="text-xs text-foreground/60 block">Estimated Churn Probability</span>
                <span className="text-4xl font-extrabold text-foreground mt-1 block">
                  {(predictionResult.prediction_probability * 100).toFixed(1)}%
                </span>
              </div>

              <div>
                <span
                  className={`inline-block px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider ${
                    predictionResult.risk_category === "High"
                      ? "bg-rose-100 text-rose-800 border border-rose-300"
                      : predictionResult.risk_category === "Medium"
                      ? "bg-amber-100 text-amber-800 border border-amber-300"
                      : "bg-emerald-100 text-emerald-800 border border-emerald-300"
                  }`}
                >
                  {predictionResult.risk_category} Churn Risk
                </span>
                <span className="text-[11px] text-foreground/50 block mt-1">
                  Predicted Class: <strong>{predictionResult.prediction_label}</strong>
                </span>
              </div>

              <div className="p-3 rounded-xl bg-surface-container text-left text-[11px] space-y-1 text-foreground/60">
                <div className="flex justify-between">
                  <span>Inference Latency:</span>
                  <strong className="text-foreground">{predictionResult.latency_ms} ms</strong>
                </div>
                <div className="flex justify-between">
                  <span>Prediction ID:</span>
                  <span className="font-mono truncate max-w-[120px]">{predictionResult.id}</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-16 text-xs text-foreground/40 my-auto">
              Configure attributes and click "Evaluate Churn Probability" to test live inference.
            </div>
          )}

          <div className="text-[10px] text-foreground/40 text-center border-t border-outline-variant/20 pt-3">
            Connected to active serialized pipeline artifact
          </div>
        </div>
      </div>

      {/* Prediction History Table */}
      <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-semibold text-foreground/80 uppercase tracking-wider">
            <History className="h-4 w-4 text-primary" />
            Recent Predictions Audit Log
          </div>
          <span className="text-xs text-foreground/50">{history?.length ?? 0} persisted records</span>
        </div>

        {loadingHistory ? (
          <div className="py-8 text-center text-xs text-foreground/50">Loading history...</div>
        ) : history && history.length > 0 ? (
          <div className="overflow-x-auto max-h-72 border border-outline-variant/20 rounded-xl">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-container sticky top-0 text-foreground/70 border-b border-outline-variant/20 text-[11px]">
                <tr>
                  <th className="px-4 py-2 font-semibold">Prediction ID</th>
                  <th className="px-4 py-2 font-semibold">Predicted Label</th>
                  <th className="px-4 py-2 font-semibold">Probability</th>
                  <th className="px-4 py-2 font-semibold">Risk Category</th>
                  <th className="px-4 py-2 font-semibold">Latency</th>
                  <th className="px-4 py-2 font-semibold">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/10 text-foreground/80">
                {history.map((h: any) => (
                  <tr key={h.id} className="hover:bg-surface-container/50">
                    <td className="px-4 py-2 font-mono text-[10px] text-foreground/60">{h.id}</td>
                    <td className="px-4 py-2 font-medium">{h.prediction_label}</td>
                    <td className="px-4 py-2 font-mono">{(h.prediction_probability * 100).toFixed(1)}%</td>
                    <td className="px-4 py-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                          h.risk_category === "High"
                            ? "bg-rose-100 text-rose-800"
                            : h.risk_category === "Medium"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-emerald-100 text-emerald-800"
                        }`}
                      >
                        {h.risk_category}
                      </span>
                    </td>
                    <td className="px-4 py-2 font-mono text-foreground/60">{h.latency_ms} ms</td>
                    <td className="px-4 py-2 text-[11px] text-foreground/50">
                      {new Date(h.created_at).toLocaleTimeString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-foreground/50">No predictions logged yet.</div>
        )}
      </div>
    </div>
  );
}
