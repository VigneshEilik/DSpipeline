import Link from "next/link";
import { ArrowRight, Activity, Database, Cpu, Layers, ShieldCheck } from "lucide-react";

export default function HomePage() {
  return (
    <main className="flex flex-col min-h-screen">
      {/* Top App Bar */}
      <header className="h-16 border-b border-outline-variant/30 bg-surface px-6 flex items-center justify-between sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-md bg-primary flex items-center justify-center text-primary-foreground font-bold shadow-sm">
            M
          </div>
          <span className="font-semibold text-lg tracking-tight">ModelOps Studio</span>
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/overview"
            className="px-5 py-2 text-sm font-medium rounded-full bg-primary text-primary-foreground hover:opacity-90 transition-all inline-flex items-center gap-2 shadow-sm"
          >
            Launch Console
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <section className="flex-1 flex flex-col items-center justify-center px-6 py-20 max-w-5xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary-container text-secondary-onContainer text-xs font-semibold uppercase tracking-wider mb-6">
          <Activity className="w-3.5 h-3.5" />
          Production-Grade ML Platform
        </div>
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-foreground max-w-3xl">
          From Data to Intelligence. <br />
          <span className="text-primary">From Experiment to Production.</span>
        </h1>
        <p className="mt-6 text-lg text-foreground/70 max-w-2xl leading-relaxed">
          Autonomous end-to-end MLOps: Automated schema validation, reproducible training pipelines, MLflow experiment tracking, model registry approvals, low-latency serving, and statistical drift detection.
        </p>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/overview"
            className="px-6 py-3 rounded-full bg-primary text-primary-foreground font-medium text-sm hover:opacity-95 shadow-elevation-1 transition flex items-center gap-2"
          >
            Open Dashboard
            <ArrowRight className="w-4 h-4" />
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
            className="px-6 py-3 rounded-full bg-surface-container text-foreground font-medium text-sm hover:bg-surface-container-high transition border border-outline-variant/40"
          >
            Swagger API Docs
          </a>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-16 text-left w-full">
          <div className="p-6 rounded-2xl bg-surface border border-outline-variant/30 shadow-sm">
            <Database className="w-6 h-6 text-primary mb-3" />
            <h3 className="font-semibold text-base">Schema Validation</h3>
            <p className="text-xs text-foreground/70 mt-1 leading-relaxed">
              Pandera-backed type checking, missing value ratio profiling, and train/serve leakage prevention.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-surface border border-outline-variant/30 shadow-sm">
            <Cpu className="w-6 h-6 text-secondary mb-3" />
            <h3 className="font-semibold text-base">Reproducible Training</h3>
            <p className="text-xs text-foreground/70 mt-1 leading-relaxed">
              ColumnTransformer + Estimator bundled into atomic joblib artifacts with MLflow tracking.
            </p>
          </div>

          <div className="p-6 rounded-2xl bg-surface border border-outline-variant/30 shadow-sm">
            <ShieldCheck className="w-6 h-6 text-tertiary mb-3" />
            <h3 className="font-semibold text-base">Lifecycle & Drift Guard</h3>
            <p className="text-xs text-foreground/70 mt-1 leading-relaxed">
              Strict approval gates, real-time prediction serving, and continuous data drift monitoring.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-outline-variant/30 py-6 px-8 text-center text-xs text-foreground/60 bg-surface">
        ModelOps Studio — Designed with Google Material 3 Principles
      </footer>
    </main>
  );
}
