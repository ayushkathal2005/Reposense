"use client";

import React, { useState } from "react";
import {
  Zap,
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  ShieldX,
  FileCode,
  Globe,
  CheckCircle2,
  GitBranch,
  Layers,
  ArrowRight,
  Search,
  RefreshCw,
  Info
} from "lucide-react";

interface DependentItem {
  symbol: string;
  type?: string;
  file?: string;
  start_line?: number;
  end_line?: number;
  relationship: string;
  depth: number;
}

interface ImpactAnalysisResponse {
  target_symbol: string;
  risk_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  risk_score: number;
  risk_factors: string[];
  direct_dependents: DependentItem[];
  indirect_dependents: DependentItem[];
  affected_files: string[];
  affected_apis: string[];
  affected_tests: string[];
  blast_radius_count: number;
  explanation?: string;
  metadata?: Record<string, any>;
}

export default function ImpactClient({ repoId }: { repoId: string }) {
  const [symbolQuery, setSymbolQuery] = useState("");
  const [filePath, setFilePath] = useState("");
  const [maxDepth, setMaxDepth] = useState(6);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ImpactAnalysisResponse | null>(null);

  const handleAnalyze = async (queryToRun?: string) => {
    const sym = queryToRun || symbolQuery;
    if (!sym.trim()) return;

    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/impact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_id: repoId,
          symbol: sym.trim(),
          file_path: filePath.trim() || undefined,
          max_depth: maxDepth
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }

      const data: ImpactAnalysisResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze change impact");
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadge = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return {
          icon: <ShieldX className="text-red-500" size={18} />,
          badge: "bg-red-50 text-red-700 border-red-300",
          barColor: "bg-red-500",
          textColor: "text-red-600"
        };
      case "HIGH":
        return {
          icon: <ShieldAlert className="text-orange-500" size={18} />,
          badge: "bg-orange-50 text-orange-700 border-orange-300",
          barColor: "bg-orange-500",
          textColor: "text-orange-600"
        };
      case "MEDIUM":
        return {
          icon: <AlertTriangle className="text-yellow-500" size={18} />,
          badge: "bg-yellow-50 text-yellow-700 border-yellow-300",
          barColor: "bg-yellow-500",
          textColor: "text-yellow-600"
        };
      case "LOW":
      default:
        return {
          icon: <ShieldCheck className="text-emerald-500" size={18} />,
          badge: "bg-emerald-50 text-emerald-700 border-emerald-300",
          barColor: "bg-emerald-500",
          textColor: "text-emerald-600"
        };
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-gh-border pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-amber-500/10 text-amber-500 border border-amber-500/20">
            <Zap size={22} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gh-text">Change Impact Analysis</h1>
            <p className="text-sm text-gh-text-secondary">
              Reverse dependency traversal to calculate the blast radius, affected APIs, and risk level before modifying code.
            </p>
          </div>
        </div>
      </div>

      {/* Query Form */}
      <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleAnalyze();
          }}
          className="space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
            <div className="md:col-span-6">
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                Target Symbol or Function Name
              </label>
              <div className="relative">
                <Search className="absolute left-3 top-2.5 text-gh-text-secondary" size={16} />
                <input
                  type="text"
                  value={symbolQuery}
                  onChange={(e) => setSymbolQuery(e.target.value)}
                  placeholder="e.g. PaymentService.process_payment, authenticate, create_order"
                  className="w-full pl-9 pr-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                  required
                />
              </div>
            </div>

            <div className="md:col-span-4">
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                File Path Hint (Optional)
              </label>
              <input
                type="text"
                value={filePath}
                onChange={(e) => setFilePath(e.target.value)}
                placeholder="e.g. services/payment.py"
                className="w-full px-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                Max Depth: {maxDepth}
              </label>
              <input
                type="range"
                min={1}
                max={10}
                value={maxDepth}
                onChange={(e) => setMaxDepth(parseInt(e.target.value))}
                className="w-full accent-blue-600 mt-2"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex flex-wrap items-center gap-2 text-xs text-gh-text-secondary">
              <span className="font-medium">Suggestions:</span>
              {["process_payment", "create_order", "OrderService", "authenticate", "save"].map((chip) => (
                <button
                  key={chip}
                  type="button"
                  onClick={() => {
                    setSymbolQuery(chip);
                    handleAnalyze(chip);
                  }}
                  className="px-2 py-0.5 rounded border border-gh-border bg-gray-50 hover:bg-gray-100 text-gh-text font-mono transition-colors"
                >
                  {chip}
                </button>
              ))}
            </div>

            <button
              type="submit"
              disabled={loading || !symbolQuery.trim()}
              className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-md transition-colors shadow-sm"
            >
              {loading ? <RefreshCw className="animate-spin" size={16} /> : <Zap size={16} />}
              {loading ? "Analyzing Impact..." : "Analyze Impact"}
            </button>
          </div>
        </form>
      </div>

      {/* Error notification */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Analysis Results */}
      {result && (
        <div className="space-y-6">
          {/* Target & Risk Banner */}
          <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gh-border">
              <div>
                <span className="text-xs uppercase font-semibold text-gh-text-secondary">Impact Assessment Target</span>
                <h2 className="text-lg font-mono font-bold text-gh-text mt-0.5">{result.target_symbol}</h2>
              </div>
              <div className="flex items-center gap-3">
                <div
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-sm font-semibold ${
                    getRiskBadge(result.risk_level).badge
                  }`}
                >
                  {getRiskBadge(result.risk_level).icon}
                  <span>{result.risk_level} RISK</span>
                </div>
                <div className="text-right">
                  <div className="text-xs text-gh-text-secondary">Risk Score</div>
                  <div className={`text-base font-bold font-mono ${getRiskBadge(result.risk_level).textColor}`}>
                    {result.risk_score.toFixed(1)} / 10.0
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
              <div className="p-3 bg-gray-50 border border-gh-border rounded-md">
                <div className="text-xs text-gh-text-secondary">Blast Radius</div>
                <div className="text-2xl font-bold font-mono text-gh-text mt-1">{result.blast_radius_count}</div>
                <div className="text-[11px] text-gh-text-secondary mt-0.5">downstream dependents</div>
              </div>

              <div className="p-3 bg-gray-50 border border-gh-border rounded-md">
                <div className="text-xs text-gh-text-secondary">Direct Callers</div>
                <div className="text-2xl font-bold font-mono text-gh-text mt-1">{result.direct_dependents.length}</div>
                <div className="text-[11px] text-gh-text-secondary mt-0.5">depth = 1 callers</div>
              </div>

              <div className="p-3 bg-gray-50 border border-gh-border rounded-md">
                <div className="text-xs text-gh-text-secondary">Affected Files</div>
                <div className="text-2xl font-bold font-mono text-gh-text mt-1">{result.affected_files.length}</div>
                <div className="text-[11px] text-gh-text-secondary mt-0.5">source files in scope</div>
              </div>

              <div className="p-3 bg-gray-50 border border-gh-border rounded-md">
                <div className="text-xs text-gh-text-secondary">Affected APIs & Tests</div>
                <div className="text-2xl font-bold font-mono text-gh-text mt-1">
                  {result.affected_apis.length + result.affected_tests.length}
                </div>
                <div className="text-[11px] text-gh-text-secondary mt-0.5">
                  {result.affected_apis.length} APIs, {result.affected_tests.length} tests
                </div>
              </div>
            </div>
          </div>

          {/* Risk Factors */}
          {result.risk_factors.length > 0 && (
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-gh-text flex items-center gap-2 mb-3">
                <AlertTriangle size={16} className="text-amber-500" />
                <span>Identified Risk Factors</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {result.risk_factors.map((factor, idx) => (
                  <div
                    key={idx}
                    className="flex items-start gap-2 p-2.5 rounded-md bg-gray-50 border border-gh-border text-xs text-gh-text"
                  >
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 mt-1.5 shrink-0" />
                    <span>{factor}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Affected APIs and Tests callouts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* APIs */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-4 shadow-sm">
              <h4 className="text-xs uppercase font-bold text-gh-text-secondary flex items-center gap-1.5 mb-2">
                <Globe size={14} className="text-blue-500" />
                <span>Affected Public APIs ({result.affected_apis.length})</span>
              </h4>
              {result.affected_apis.length > 0 ? (
                <div className="space-y-1.5">
                  {result.affected_apis.map((api, idx) => (
                    <div
                      key={idx}
                      className="px-2.5 py-1.5 rounded bg-blue-50/50 border border-blue-200 text-xs font-mono text-blue-900"
                    >
                      {api}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-gh-text-secondary italic">No public API endpoints directly impacted.</p>
              )}
            </div>

            {/* Tests */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-4 shadow-sm">
              <h4 className="text-xs uppercase font-bold text-gh-text-secondary flex items-center gap-1.5 mb-2">
                <CheckCircle2 size={14} className="text-emerald-500" />
                <span>Affected Test Coverage ({result.affected_tests.length})</span>
              </h4>
              {result.affected_tests.length > 0 ? (
                <div className="space-y-1.5">
                  {result.affected_tests.map((test, idx) => (
                    <div
                      key={idx}
                      className="px-2.5 py-1.5 rounded bg-emerald-50/50 border border-emerald-200 text-xs font-mono text-emerald-900"
                    >
                      {test}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-xs text-amber-700 italic bg-amber-50 p-2 rounded border border-amber-200">
                  Warning: No test files were found calling this symbol or its dependents.
                </p>
              )}
            </div>
          </div>

          {/* Direct Callers Hierarchy */}
          <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
            <h3 className="text-sm font-semibold text-gh-text flex items-center gap-2 mb-3">
              <GitBranch size={16} className="text-blue-500" />
              <span>Direct Callers (Depth 1)</span>
              <span className="text-xs text-gh-text-secondary">({result.direct_dependents.length})</span>
            </h3>

            {result.direct_dependents.length > 0 ? (
              <div className="divide-y divide-gh-border border border-gh-border rounded-md overflow-hidden">
                {result.direct_dependents.map((dep, idx) => (
                  <div key={idx} className="p-3 bg-gh-bg hover:bg-gray-50 flex items-center justify-between gap-4">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-gh-text">{dep.symbol}</span>
                        {dep.type && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                            {dep.type}
                          </span>
                        )}
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-blue-50 text-blue-700 border border-blue-200">
                          {dep.relationship}
                        </span>
                      </div>
                      {dep.file && (
                        <div className="text-xs text-gh-text-secondary font-mono">
                          {dep.file}
                          {dep.start_line ? `:${dep.start_line}` : ""}
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-gh-text-secondary font-mono shrink-0">depth: {dep.depth}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-gh-text-secondary italic">No direct callers found in repository graph.</p>
            )}
          </div>

          {/* Indirect Dependents */}
          {result.indirect_dependents.length > 0 && (
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-gh-text flex items-center gap-2 mb-3">
                <Layers size={16} className="text-purple-500" />
                <span>Indirect Transitive Dependents</span>
                <span className="text-xs text-gh-text-secondary">({result.indirect_dependents.length})</span>
              </h3>

              <div className="divide-y divide-gh-border border border-gh-border rounded-md overflow-hidden">
                {result.indirect_dependents.map((dep, idx) => (
                  <div key={idx} className="p-3 bg-gh-bg hover:bg-gray-50 flex items-center justify-between gap-4">
                    <div className="space-y-0.5">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-gh-text">{dep.symbol}</span>
                        {dep.type && (
                          <span className="px-1.5 py-0.5 rounded text-[10px] uppercase font-semibold bg-gray-100 text-gray-700 border border-gray-200">
                            {dep.type}
                          </span>
                        )}
                        <span className="px-1.5 py-0.5 rounded text-[10px] bg-purple-50 text-purple-700 border border-purple-200">
                          {dep.relationship}
                        </span>
                      </div>
                      {dep.file && (
                        <div className="text-xs text-gh-text-secondary font-mono">
                          {dep.file}
                          {dep.start_line ? `:${dep.start_line}` : ""}
                        </div>
                      )}
                    </div>
                    <span className="text-xs text-gh-text-secondary font-mono shrink-0">depth: {dep.depth}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Grounded Explanation Narrative */}
          {result.explanation && (
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-gh-text flex items-center gap-2 mb-3">
                <Info size={16} className="text-blue-500" />
                <span>Synthesized Impact Summary</span>
              </h3>
              <div className="p-4 bg-gray-50 rounded-md border border-gh-border font-mono text-xs text-gh-text whitespace-pre-wrap leading-relaxed">
                {result.explanation}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
