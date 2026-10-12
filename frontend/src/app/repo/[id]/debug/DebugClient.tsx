"use client";

import React, { useState } from "react";
import {
  Bug,
  AlertTriangle,
  CheckCircle2,
  HelpCircle,
  Code2,
  FileText,
  Search,
  RefreshCw,
  GitBranch,
  Wrench,
  ShieldAlert,
  ShieldCheck,
  Info,
  ChevronRight,
  Terminal
} from "lucide-react";

interface FailureLocation {
  file: string;
  line?: number;
  symbol?: string;
  code_snippet?: string;
  relevance_score: number;
}

interface DebugAnalysisResponse {
  error_summary: string;
  likely_locations: FailureLocation[];
  facts: string[];
  inferences: string[];
  possible_causes: string[];
  possible_fixes: string[];
  related_callers: string[];
  confidence: "High" | "Medium" | "Low";
  explanation?: string;
  metadata?: Record<string, any>;
}

export default function DebugClient({ repoId }: { repoId: string }) {
  const [errorMessage, setErrorMessage] = useState("");
  const [stackTrace, setStackTrace] = useState("");
  const [symbolHint, setSymbolHint] = useState("");
  const [filePathHint, setFilePathHint] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DebugAnalysisResponse | null>(null);

  const presets = [
    {
      label: "KeyError: 'user_id'",
      msg: "KeyError: 'user_id'",
      trace: `File "src/api/users.py", line 81, in get_user_profile\n    return user_data["user_id"]`,
      sym: "get_user_profile"
    },
    {
      label: "NoneType AttributeError",
      msg: "AttributeError: 'NoneType' object has no attribute 'charge'",
      trace: `File "src/services/payment.py", line 42, in process_payment\n    gateway.charge(amount)`,
      sym: "process_payment"
    },
    {
      label: "JS TypeError undefined",
      msg: "TypeError: Cannot read properties of undefined (reading 'charge')",
      trace: `TypeError: Cannot read properties of undefined (reading 'charge')\n    at PaymentService.charge (src/payment.js:45:12)\n    at OrderController.checkout (src/order.js:20:8)`,
      sym: "PaymentService.charge"
    }
  ];

  const handleRunAnalysis = async (customMsg?: string, customTrace?: string, customSym?: string) => {
    const msg = customMsg !== undefined ? customMsg : errorMessage;
    const trace = customTrace !== undefined ? customTrace : stackTrace;
    const sym = customSym !== undefined ? customSym : symbolHint;

    if (!msg.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/api/debug", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_id: repoId,
          error_message: msg.trim(),
          stack_trace: trace.trim() || undefined,
          file_path: filePathHint.trim() || undefined,
          symbol: sym.trim() || undefined
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }

      const data: DebugAnalysisResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to analyze error");
    } finally {
      setLoading(false);
    }
  };

  const applyPreset = (p: typeof presets[0]) => {
    setErrorMessage(p.msg);
    setStackTrace(p.trace);
    setSymbolHint(p.sym);
    handleRunAnalysis(p.msg, p.trace, p.sym);
  };

  const getConfidenceBadge = (confidence: string) => {
    switch (confidence) {
      case "High":
        return {
          icon: <ShieldCheck size={16} className="text-emerald-500" />,
          badge: "bg-emerald-50 text-emerald-700 border-emerald-300",
          text: "High Confidence"
        };
      case "Medium":
        return {
          icon: <AlertTriangle size={16} className="text-amber-500" />,
          badge: "bg-amber-50 text-amber-700 border-amber-300",
          text: "Medium Confidence"
        };
      case "Low":
      default:
        return {
          icon: <Info size={16} className="text-gray-500" />,
          badge: "bg-gray-50 text-gray-700 border-gray-300",
          text: "Low Confidence"
        };
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-gh-border pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-rose-500/10 text-rose-500 border border-rose-500/20">
            <Bug size={22} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gh-text">Repository-Aware Debugging</h1>
            <p className="text-sm text-gh-text-secondary">
              Grounded static analysis + call-path inspection to identify root causes and rigorously distinguish FACT, INFERENCE, and POSSIBLE CAUSE.
            </p>
          </div>
        </div>
      </div>

      {/* Input Form */}
      <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleRunAnalysis();
          }}
          className="space-y-4"
        >
          <div>
            <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
              Error Message or Exception String
            </label>
            <div className="relative">
              <Terminal className="absolute left-3 top-2.5 text-gh-text-secondary" size={16} />
              <input
                type="text"
                value={errorMessage}
                onChange={(e) => setErrorMessage(e.target.value)}
                placeholder="e.g. KeyError: 'user_id' or AttributeError: 'NoneType' object has no attribute 'charge'"
                className="w-full pl-9 pr-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
              Stack Trace / Traceback (Optional)
            </label>
            <textarea
              rows={3}
              value={stackTrace}
              onChange={(e) => setStackTrace(e.target.value)}
              placeholder="Paste Python traceback or Node.js error trace here..."
              className="w-full px-3 py-2 text-xs bg-gray-50 border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono text-gh-text"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                Symbol Hint (Optional)
              </label>
              <input
                type="text"
                value={symbolHint}
                onChange={(e) => setSymbolHint(e.target.value)}
                placeholder="e.g. get_user_profile, UserService"
                className="w-full px-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-1">
                File Path Hint (Optional)
              </label>
              <input
                type="text"
                value={filePathHint}
                onChange={(e) => setFilePathHint(e.target.value)}
                placeholder="e.g. src/api/users.py"
                className="w-full px-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
              />
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
            <div className="flex flex-wrap items-center gap-2 text-xs text-gh-text-secondary">
              <span className="font-medium">Preset Scenarios:</span>
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
              disabled={loading || !errorMessage.trim()}
              className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-md transition-colors shadow-sm"
            >
              {loading ? <RefreshCw className="animate-spin" size={16} /> : <Bug size={16} />}
              {loading ? "Diagnosing..." : "Analyze Root Cause"}
            </button>
          </div>
        </form>
      </div>

      {/* Error banner */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Debug Results */}
      {result && (
        <div className="space-y-6">
          {/* Header Summary */}
          <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-gh-border">
              <div>
                <span className="text-xs uppercase font-semibold text-gh-text-secondary">Diagnosed Exception</span>
                <h2 className="text-base font-mono font-bold text-red-600 mt-0.5">{result.error_summary}</h2>
              </div>
              <div
                className={`flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-semibold ${
                  getConfidenceBadge(result.confidence).badge
                }`}
              >
                {getConfidenceBadge(result.confidence).icon}
                <span>{getConfidenceBadge(result.confidence).text}</span>
              </div>
            </div>

            {/* Likely Failure Locations */}
            {result.likely_locations.length > 0 && (
              <div className="mt-4 space-y-3">
                <h3 className="text-xs uppercase font-bold text-gh-text-secondary flex items-center gap-1.5">
                  <FileText size={14} className="text-blue-500" />
                  <span>Likely Failure Location(s)</span>
                </h3>
                <div className="space-y-2">
                  {result.likely_locations.map((loc, idx) => (
                    <div key={idx} className="p-3 bg-gray-50 border border-gh-border rounded-md font-mono text-xs">
                      <div className="flex items-center justify-between font-semibold text-gh-text mb-1">
                        <span>
                          {loc.file}
                          {loc.line ? `:${loc.line}` : ""}
                        </span>
                        {loc.symbol && (
                          <span className="px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 text-[10px]">
                            {loc.symbol}
                          </span>
                        )}
                      </div>
                      {loc.code_snippet && (
                        <pre className="mt-2 p-2.5 bg-gray-900 text-gray-100 rounded text-[11px] overflow-x-auto whitespace-pre">
                          {loc.code_snippet}
                        </pre>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Strict Evidence Quadrants: FACTS, INFERENCES, CAUSES, FIXES */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* FACTS */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-3">
              <h3 className="text-xs uppercase font-bold text-emerald-700 flex items-center gap-2">
                <CheckCircle2 size={16} className="text-emerald-600" />
                <span>Verified Facts (Ground Truth)</span>
              </h3>
              <div className="space-y-2">
                {result.facts.map((fact, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-emerald-50/50 border border-emerald-200 text-xs text-emerald-950 font-sans"
                  >
                    • {fact}
                  </div>
                ))}
              </div>
            </div>

            {/* INFERENCES */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-3">
              <h3 className="text-xs uppercase font-bold text-blue-700 flex items-center gap-2">
                <Info size={16} className="text-blue-600" />
                <span>Inferences (Architectural Deductions)</span>
              </h3>
              <div className="space-y-2">
                {result.inferences.map((inf, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-blue-50/50 border border-blue-200 text-xs text-blue-950 font-sans"
                  >
                    • {inf}
                  </div>
                ))}
              </div>
            </div>

            {/* POSSIBLE CAUSES */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-3">
              <h3 className="text-xs uppercase font-bold text-amber-700 flex items-center gap-2">
                <AlertTriangle size={16} className="text-amber-600" />
                <span>Possible Root Causes</span>
              </h3>
              <div className="space-y-2">
                {result.possible_causes.map((cause, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-amber-50/50 border border-amber-200 text-xs text-amber-950 font-sans"
                  >
                    • {cause}
                  </div>
                ))}
              </div>
            </div>

            {/* RECOMMENDED FIXES */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-3">
              <h3 className="text-xs uppercase font-bold text-purple-700 flex items-center gap-2">
                <Wrench size={16} className="text-purple-600" />
                <span>Recommended Fixes</span>
              </h3>
              <div className="space-y-2">
                {result.possible_fixes.map((fix, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded bg-purple-50/50 border border-purple-200 text-xs text-purple-950 font-mono"
                  >
                    • {fix}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Related Callers */}
          {result.related_callers.length > 0 && (
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
              <h3 className="text-xs uppercase font-bold text-gh-text-secondary flex items-center gap-1.5 mb-3">
                <GitBranch size={14} className="text-blue-500" />
                <span>Upstream Callers / Invocations ({result.related_callers.length})</span>
              </h3>
              <div className="flex flex-wrap gap-2">
                {result.related_callers.map((caller, idx) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 rounded bg-gray-100 border border-gh-border font-mono text-xs text-gh-text"
                  >
                    {caller}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Synthesized Diagnostic Explanation */}
          {result.explanation && (
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
              <h3 className="text-sm font-semibold text-gh-text flex items-center gap-2 mb-3">
                <Code2 size={16} className="text-blue-500" />
                <span>Synthesized Debugging Report</span>
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
