"use client";

import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import {
  Database,
  Upload,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileText,
  Play,
  Table as TableIcon,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { api } from "@/services/api";

export default function DatasetsPage() {
  const queryClient = useQueryClient();
  const [selectedDatasetId, setSelectedDatasetId] = useState<string | null>(null);
  const [previewPage, setPreviewPage] = useState(1);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadName, setUploadName] = useState("");
  const [uploadDesc, setUploadDesc] = useState("");
  const [uploadError, setUploadError] = useState<string | null>(null);

  // Queries
  const { data: datasets, isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => api.getDatasets(),
  });

  const { data: selectedDataset } = useQuery({
    queryKey: ["dataset", selectedDatasetId],
    queryFn: () => (selectedDatasetId ? api.getDataset(selectedDatasetId) : null),
    enabled: !!selectedDatasetId,
  });

  const { data: preview, isLoading: loadingPreview } = useQuery({
    queryKey: ["dataset-preview", selectedDatasetId, previewPage],
    queryFn: () => (selectedDatasetId ? api.getDatasetPreview(selectedDatasetId, previewPage, 10) : null),
    enabled: !!selectedDatasetId,
  });

  // Upload Mutation
  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!uploadFile || !uploadName) throw new Error("Please provide a name and select a CSV file.");
      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("name", uploadName);
      if (uploadDesc) formData.append("description", uploadDesc);
      formData.append("target_column", "Churn");
      return api.uploadDataset(formData);
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      setUploadOpen(false);
      setUploadFile(null);
      setUploadName("");
      setUploadDesc("");
      setSelectedDatasetId(data.id);
    },
    onError: (err: any) => {
      setUploadError(err.message || "Failed to upload dataset.");
    },
  });

  return (
    <div className="space-y-6">
      {/* Header & Upload Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Datasets & Schema Validation</h1>
          <p className="text-xs text-foreground/60 mt-1">
            Upload raw customer datasets, inspect automated validation reports, and review feature schemas.
          </p>
        </div>
        <button
          onClick={() => setUploadOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition shadow-xs"
        >
          <Upload className="h-3.5 w-3.5" />
          Upload Dataset (CSV)
        </button>
      </div>

      {/* Upload Modal */}
      {uploadOpen && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <div className="bg-surface rounded-2xl border border-outline-variant/30 p-6 w-full max-w-lg shadow-elevation-2 space-y-4">
            <h2 className="text-base font-semibold text-foreground">Upload Customer Dataset</h2>

            {uploadError && (
              <div className="p-3 rounded-xl bg-error-container text-error-onContainer text-xs flex items-center gap-2">
                <XCircle className="h-4 w-4 shrink-0" />
                {uploadError}
              </div>
            )}

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-medium text-foreground block mb-1">Dataset Name *</label>
                <input
                  type="text"
                  value={uploadName}
                  onChange={(e) => setUploadName(e.target.value)}
                  placeholder="e.g., Telco Churn Q3 Cohort"
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">Description</label>
                <textarea
                  value={uploadDesc}
                  onChange={(e) => setUploadDesc(e.target.value)}
                  placeholder="Optional description of dataset source and lineage"
                  rows={2}
                  className="w-full px-3 py-2 rounded-xl bg-surface-container border border-outline-variant/40 focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="font-medium text-foreground block mb-1">CSV File *</label>
                <input
                  type="file"
                  accept=".csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-primary-container file:text-primary-onContainer hover:file:opacity-90"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                onClick={() => setUploadOpen(false)}
                className="px-4 py-2 rounded-full border border-outline-variant/40 text-xs font-medium text-foreground hover:bg-surface-container transition"
              >
                Cancel
              </button>
              <button
                disabled={uploadMutation.isPending}
                onClick={() => uploadMutation.mutate()}
                className="px-5 py-2 rounded-full bg-primary text-primary-foreground text-xs font-medium hover:opacity-90 transition disabled:opacity-50 inline-flex items-center gap-2"
              >
                {uploadMutation.isPending && <Loader2 className="h-3.5 w-3.5 animate-spin" />}
                Validate & Upload
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Datasets Table & Details View */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Datasets List */}
        <div className="lg:col-span-1 rounded-2xl border border-outline-variant/30 bg-surface p-4 shadow-xs">
          <span className="text-xs font-semibold text-foreground/70 uppercase tracking-wider block mb-3 px-2">
            Available Datasets ({datasets?.length ?? 0})
          </span>

          {isLoading ? (
            <div className="py-8 text-center text-xs text-foreground/50">Loading datasets...</div>
          ) : datasets && datasets.length > 0 ? (
            <div className="space-y-1.5">
              {datasets.map((d: any) => {
                const isSelected = selectedDatasetId === d.id || (!selectedDatasetId && datasets[0].id === d.id);
                return (
                  <button
                    key={d.id}
                    onClick={() => {
                      setSelectedDatasetId(d.id);
                      setPreviewPage(1);
                    }}
                    className={`w-full text-left p-3 rounded-xl transition text-xs flex flex-col gap-1 border ${
                      isSelected
                        ? "bg-primary-container/30 border-primary/40 text-foreground"
                        : "bg-surface hover:bg-surface-container border-transparent text-foreground/80"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-foreground truncate">{d.name}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                          d.status === "PASSED"
                            ? "bg-emerald-100 text-emerald-800"
                            : d.status === "WARNINGS"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-rose-100 text-rose-800"
                        }`}
                      >
                        {d.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[11px] text-foreground/50">
                      <span>{d.total_rows} rows</span>
                      <span>•</span>
                      <span>v{d.latest_version ?? 1}</span>
                    </div>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-foreground/50">
              No datasets uploaded yet. Click Upload Dataset above.
            </div>
          )}
        </div>

        {/* Selected Dataset Detail & Preview */}
        <div className="lg:col-span-2 space-y-6">
          {selectedDataset ? (
            <>
              {/* Detail & Validation Card */}
              <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-bold text-foreground">{selectedDataset.name}</h2>
                    <p className="text-xs text-foreground/60">{selectedDataset.description || "No description provided."}</p>
                  </div>
                  <Link
                    href={`/experiments?dataset_version_id=${selectedDataset.versions[0]?.id}`}
                    className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-secondary-container text-secondary-onContainer text-xs font-medium hover:opacity-90 transition self-start shadow-xs"
                  >
                    <Play className="h-3.5 w-3.5" />
                    Train Model on Dataset
                  </Link>
                </div>

                {/* Validation Summary */}
                {selectedDataset.latest_validation && (
                  <div className="p-4 rounded-xl bg-surface-container space-y-2 text-xs">
                    <div className="flex items-center gap-2">
                      {selectedDataset.latest_validation.is_valid ? (
                        <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                      ) : (
                        <AlertTriangle className="h-4 w-4 text-rose-600" />
                      )}
                      <span className="font-semibold text-foreground">
                        Validation Status: {selectedDataset.latest_validation.status}
                      </span>
                    </div>
                    {selectedDataset.latest_validation.warnings?.length > 0 && (
                      <ul className="list-disc pl-5 text-[11px] text-amber-700">
                        {selectedDataset.latest_validation.warnings.map((w: string, i: number) => (
                          <li key={i}>{w}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}
              </div>

              {/* Data Preview Card */}
              <div className="rounded-2xl border border-outline-variant/30 bg-surface p-6 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs font-semibold text-foreground/80 uppercase tracking-wider">
                    <TableIcon className="h-4 w-4 text-primary" />
                    Data Preview (Page {previewPage})
                  </div>
                  <div className="flex items-center gap-1 text-xs">
                    <button
                      disabled={previewPage <= 1}
                      onClick={() => setPreviewPage((p) => Math.max(1, p - 1))}
                      className="p-1 rounded-lg border border-outline-variant/30 hover:bg-surface-container disabled:opacity-30"
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </button>
                    <span className="px-2 text-foreground/70">Page {previewPage}</span>
                    <button
                      disabled={!preview || preview.rows.length < 10}
                      onClick={() => setPreviewPage((p) => p + 1)}
                      className="p-1 rounded-lg border border-outline-variant/30 hover:bg-surface-container disabled:opacity-30"
                    >
                      <ChevronRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {loadingPreview ? (
                  <div className="py-12 text-center text-xs text-foreground/50">Loading preview...</div>
                ) : preview && preview.rows.length > 0 ? (
                  <div className="overflow-x-auto max-h-96 border border-outline-variant/20 rounded-xl">
                    <table className="w-full text-[11px] text-left">
                      <thead className="bg-surface-container sticky top-0 text-foreground/70 border-b border-outline-variant/20">
                        <tr>
                          {preview.columns.map((col: string) => (
                            <th key={col} className="px-3 py-2 font-semibold whitespace-nowrap">
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-outline-variant/10 text-foreground/80">
                        {preview.rows.map((row: any, rIdx: number) => (
                          <tr key={rIdx} className="hover:bg-surface-container/50">
                            {preview.columns.map((col: string) => (
                              <td key={col} className="px-3 py-1.5 whitespace-nowrap">
                                {String(row[col])}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="py-12 text-center text-xs text-foreground/50">No rows found in preview.</div>
                )}
              </div>
            </>
          ) : (
            <div className="py-16 text-center text-xs text-foreground/40 bg-surface rounded-2xl border border-outline-variant/30">
              Select a dataset from the left column to view its schema and live preview.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
