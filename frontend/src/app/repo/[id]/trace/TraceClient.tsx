"use client";

import React, { useState } from "react";
import {
  GitCommit,
  ArrowDown,
  Search,
  RefreshCw,
  FileCode,
  ShieldCheck,
  AlertTriangle,
  Play,
  Layers,
  ChevronRight,
  Info
} from "lucide-react";

interface TraceStep {
  order: number;
  symbol: string;
  file?: string;
  line?: number;
  relationship: string;
  evidence?: string;
}

interface ExecutionTrace {
  entrypoint: string;
  target?: string;
  steps: TraceStep[];
  confidence: "high" | "medium" | "low";
  unresolved_steps: string[];
  explanation?: string;
}

export default function TraceClient({ repoId }: { repoId: string }) {
  const [entrypoint, setEntrypoint] = useState("");
  const [target, setTarget] = useState("");
  const [maxDepth, setMaxDepth] = useState(6);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExecutionTrace | null>(null);

  const presets = [
    { label: "Create Order Workflow", entry: "create_order_endpoint", tgt: "OrderRepository.save" },
    { label: "Checkout & Payment Flow", entry: "OrderController.checkout", tgt: "StripeGateway.charge" },
    { label: "User Login & Auth", entry: "login", tgt: "verify_password" },
  ];

  const handleTrace = async (customEntry?: string, customTgt?: string) => {
    const entry = customEntry !== undefined ? customEntry : entrypoint;
    const tgt = customTgt !== undefined ? customTgt : target;

    if (!entry.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/api/trace", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_id: repoId,
          entrypoint: entry.trim(),
          target: tgt.trim() || undefined,
          max_depth: maxDepth
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }

      const data: ExecutionTrace = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to trace execution path");
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = (p: typeof presets[0]) => {
    setEntrypoint(p.entry);
    setTarget(p.tgt);
    handleTrace(p.entry, p.tgt);
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-gh-border pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-600 border border-emerald-500/20">
            <GitCommit size={22} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gh-text">Execution Flow Tracing</h1>
            <p className="text-sm text-gh-text-secondary">
              Deterministic step-by-step call graph traversal from entrypoint to terminal destination without hallucinated hops.
            </p>
          </div>
        </div>
      </div>

      {/* Query Form */}
      <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleTrace();
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div className="md:col-span-6">
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                Entrypoint Symbol or Intent
              </label>
              <div className="relative">
                <Play className="absolute left-3 top-2.5 text-gh-text-secondary" size={16} />
                <input
                  type="text"
                  value={entrypoint}
                  onChange={(e) => setEntrypoint(e.target.value)}
                  placeholder="e.g. create_order_endpoint, login, or POST /api/orders"
                  className="w-full pl-9 pr-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                  required
                />
              </div>
            </div>

            <div className="md:col-span-4">
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                Target Terminal Symbol (Optional)
              </label>
              <input
                type="text"
                value={target}
                onChange={(e) => setTarget(e.target.value)}
                placeholder="e.g. OrderRepository.save, Database.insert"
                className="w-full px-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                Max Hops: {maxDepth}
              </label>
              <input
                type="range"
                min={2}
                max={12}
                value={maxDepth}
                onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                className="w-full accent-blue-600 mt-2"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex flex-wrap items-center gap-2 text-xs text-gh-text-secondary">
              <span className="font-medium">Workflow Presets:</span>
              {presets.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => applyPreset(p)}
                  className="px-2.5 py-1 rounded border border-gh-border bg-gray-50 hover:bg-gray-100 text-gh-text font-mono transition-colors"
                >
                  {p.label}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={loading || !entrypoint.trim()}
              className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-md transition-colors shadow-sm"
            >
              {loading ? <RefreshCw className="animate-spin" size={16} /> : <Play size={16} />}
              {loading ? "Tracing Path..." : "Trace Path"}
            </button>
          </div>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Result Display */}
      {result && (
        <div className="space-y-6">
          {/* Header Card */}
          <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
              <div className="text-xs uppercase font-semibold text-gh-text-secondary">Traced Path</div>
              <h2 className="text-base font-mono font-bold text-gh-text mt-0.5">
                {result.entrypoint} {result.target ? `→ ${result.target}` : ""}
              </h2>
              <div className="text-xs text-gh-text-secondary mt-1">
                {result.steps.length} sequential execution steps discovered
              </div>
            </div>

            <div className="flex items-center gap-3">
              <span
                className={`text-xs font-semibold px-3 py-1.5 rounded-full border ${
                  result.confidence === "high"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-300"
                    : result.confidence === "medium"
                    ? "bg-amber-50 text-amber-700 border-amber-300"
                    : "bg-gray-50 text-gray-700 border-gray-300"
                }`}
              >
                {result.confidence.toUpperCase()} CONFIDENCE
              </span>
            </div>
          </div>

          {/* Stepper Flow Cards */}
          <div className="bg-gh-bg border border-gh-border rounded-lg p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gh-text mb-6">Execution Path Steps</h3>
            <div className="space-y-4">
              {result.steps.map((step, idx) => (
                <div key={idx} className="relative">
                  <div className="flex items-start gap-4 p-4 rounded-lg bg-gray-50 border border-gh-border hover:border-blue-400 transition-colors">
                    {/* Step number badge */}
                    <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-mono text-xs font-bold flex items-center justify-center shrink-0 border border-blue-200">
                      {step.order}
                    </div>

                    <div className="flex-1 space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-sm font-bold text-gh-text">{step.symbol}</span>
                        <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                          {step.relationship}
                        </span>
                      </div>

                      {step.file && (
                        <div className="text-xs font-mono text-gh-text-secondary flex items-center gap-1.5">
                          <FileCode size={13} />
                          <span>
                            {step.file}
                            {step.line ? `:${step.line}` : ""}
                          </span>
                        </div>
                      )}

                      {step.evidence && (
                        <p className="text-xs text-gh-text font-mono bg-white p-2 rounded border border-gh-border mt-1">
                          {step.evidence}
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Connecting Arrow */}
                  {idx < result.steps.length - 1 && (
                    <div className="flex justify-center my-2 text-gray-400">
                      <ArrowDown size={18} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Grounded Path Explanation */}
          {result.explanation && (
            <div className="bg-gh-bg border border-gh-border rounded-lg p-6 shadow-sm">
              <h3 className="text-sm font-semibold text-gh-text mb-3">Grounded Path Assessment</h3>
              <div className="prose prose-sm max-w-none text-xs font-mono text-gh-text bg-gray-50 p-4 rounded-md border border-gh-border whitespace-pre-wrap leading-relaxed">
                {result.explanation}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
