"use client";

import React, { useState } from "react";
import {
  BookOpen,
  FileCode2,
  Layers,
  Network,
  Code,
  Copy,
  Check,
  Download,
  RefreshCw,
  Search,
  ExternalLink,
  ChevronRight,
  GitBranch
} from "lucide-react";

interface SymbolDoc {
  name: string;
  type?: string;
  file?: string;
  start_line?: number;
  end_line?: number;
  signature?: string;
  docstring?: string;
  callers: string[];
  callees: string[];
  dependencies: string[];
  evidence_sources: string[];
}

interface DocumentationResponse {
  title: string;
  doc_type: string;
  target: string;
  markdown_content: string;
  symbols: SymbolDoc[];
  diagram_mermaid?: string;
  metadata?: Record<string, any>;
}

export default function DocsClient({ repoId }: { repoId: string }) {
  const [docType, setDocType] = useState<"api" | "function" | "module" | "architecture">("api");
  const [target, setTarget] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DocumentationResponse | null>(null);
  const [copied, setCopied] = useState(false);

  const docTypes = [
    { id: "api", label: "API Endpoints", icon: Network, desc: "REST routes, controllers, and downstream services" },
    { id: "function", label: "Function / Symbol", icon: Code, desc: "Deep dive into callers, callees, and signatures" },
    { id: "module", label: "Module / File", icon: FileCode2, desc: "Complete documentation of a specific module file" },
    { id: "architecture", label: "Architecture", icon: Layers, desc: "High-level layers and interactive flow diagram" },
  ];

  const handleGenerate = async (overrideType?: typeof docType, overrideTarget?: string) => {
    const t = overrideType || docType;
    const tgt = overrideTarget !== undefined ? overrideTarget : target;

    setLoading(true);
    setError(null);

    try {
      const res = await fetch("http://localhost:8000/api/documentation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo_id: repoId,
          doc_type: t,
          target: tgt.trim() || undefined
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Server returned ${res.status}`);
      }

      const data: DocumentationResponse = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "Failed to generate documentation");
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    if (!result) return;
    navigator.clipboard.writeText(result.markdown_content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadMarkdown = () => {
    if (!result) return;
    const blob = new Blob([result.markdown_content], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${result.doc_type}_docs.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-gh-border pb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-indigo-500/10 text-indigo-500 border border-indigo-500/20">
            <BookOpen size={22} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gh-text">Repository Documentation Intelligence</h1>
            <p className="text-sm text-gh-text-secondary">
              Evidence-backed API, function, module, and architecture documentation grounded directly in verified static analysis.
            </p>
          </div>
        </div>
      </div>

      {/* Mode Selector */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {docTypes.map((dt) => {
          const Icon = dt.icon;
          const isSelected = docType === dt.id;
          return (
            <button
              key={dt.id}
              type="button"
              onClick={() => {
                setDocType(dt.id as any);
                handleGenerate(dt.id as any);
              }}
              className={`p-4 rounded-lg border text-left transition-all ${
                isSelected
                  ? "bg-blue-50/50 border-blue-500 ring-1 ring-blue-500 shadow-sm"
                  : "bg-gh-bg border-gh-border hover:bg-gray-50"
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <Icon size={16} className={isSelected ? "text-blue-600" : "text-gh-text-secondary"} />
                <span className={`text-sm font-semibold ${isSelected ? "text-blue-900" : "text-gh-text"}`}>
                  {dt.label}
                </span>
              </div>
              <p className="text-xs text-gh-text-secondary">{dt.desc}</p>
            </button>
          );
        })}
      </div>

      {/* Target input form */}
      <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-4">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleGenerate();
          }}
          className="flex flex-col sm:flex-row items-center gap-3"
        >
          <div className="relative flex-1 w-full">
            <Search className="absolute left-3 top-2.5 text-gh-text-secondary" size={16} />
            <input
              type="text"
              value={target}
              onChange={(e) => setTarget(e.target.value)}
              placeholder={
                docType === "api"
                  ? "Filter by path or symbol (e.g. /api/orders, checkout)... (leave empty for all)"
                  : docType === "function"
                  ? "Enter function or symbol name (e.g. OrderService.create_order, process_payment)..."
                  : docType === "module"
                  ? "Enter file or module path (e.g. src/services/order_service.py)..."
                  : "System architecture overview (optional target)..."
              }
              className="w-full pl-9 pr-3 py-2 text-sm bg-gh-bg border border-gh-border rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono text-gh-text"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded-md transition-colors shadow-sm shrink-0 w-full sm:w-auto justify-center"
          >
            {loading ? <RefreshCw className="animate-spin" size={16} /> : <BookOpen size={16} />}
            {loading ? "Generating..." : "Generate Docs"}
          </button>
        </form>
      </div>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Results View */}
      {result && (
        <div className="space-y-6">
          {/* Header Action Bar */}
          <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                  {result.doc_type}
                </span>
                <h2 className="text-base font-bold text-gh-text">{result.title}</h2>
              </div>
              <p className="text-xs text-gh-text-secondary mt-1">
                Target: <span className="font-mono text-gh-text font-semibold">{result.target}</span> • {result.symbols.length} symbols documented
              </p>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={copyToClipboard}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-gh-border rounded-md hover:bg-gray-50 text-gh-text transition-colors"
              >
                {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                <span>{copied ? "Copied!" : "Copy Markdown"}</span>
              </button>
              <button
                type="button"
                onClick={downloadMarkdown}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-gh-border rounded-md hover:bg-gray-50 text-gh-text transition-colors"
              >
                <Download size={14} />
                <span>Export .md</span>
              </button>
            </div>
          </div>

          {/* Documented Symbols Overview */}
          {result.symbols.length > 0 && (
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm">
              <h3 className="text-xs uppercase font-bold text-gh-text-secondary flex items-center gap-1.5 mb-3">
                <GitBranch size={14} className="text-blue-500" />
                <span>Indexed Code Entities ({result.symbols.length})</span>
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {result.symbols.map((sym, idx) => (
                  <div key={idx} className="p-3 bg-gray-50 border border-gh-border rounded-md text-xs">
                    <div className="flex items-center justify-between font-mono font-semibold text-gh-text">
                      <span>{sym.name}</span>
                      {sym.type && (
                        <span className="px-1.5 py-0.5 rounded bg-gray-200 text-gray-800 text-[10px]">
                          {sym.type}
                        </span>
                      )}
                    </div>
                    {sym.file && (
                      <div className="text-[11px] text-gh-text-secondary font-mono mt-0.5">
                        {sym.file}
                        {sym.start_line ? `:${sym.start_line}` : ""}
                      </div>
                    )}
                    {sym.callees.length > 0 && (
                      <div className="mt-2 text-[11px] text-gh-text">
                        <span className="font-semibold text-gh-text-secondary">Downstream: </span>
                        {sym.callees.slice(0, 3).join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Markdown Content Display */}
          <div className="bg-gh-bg border border-gh-border rounded-lg p-6 shadow-sm">
            <h3 className="text-sm font-semibold text-gh-text mb-4 pb-2 border-b border-gh-border">
              Documentation Content
            </h3>
            <div className="prose prose-sm max-w-none text-gh-text font-mono text-xs whitespace-pre-wrap leading-relaxed bg-gray-50 p-5 rounded-md border border-gh-border">
              {result.markdown_content}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
