"use client";

import React, { useEffect, useState } from "react";
import {
  Network,
  Box,
  FileText,
  Share2,
  Layers,
  AlertCircle,
  RefreshCw,
  Code,
  Copy,
  Check,
  Download,
  Info,
  ChevronRight,
  ExternalLink
} from "lucide-react";

interface ComponentItem {
  id: string;
  name: string;
  role: string;
  file?: string;
  start_line?: number;
  end_line?: number;
  docstring?: string;
  outgoing_calls: string[];
}

interface RelationshipItem {
  source: string;
  target: string;
  source_role: string;
  target_role: string;
  relationship: string;
  call_count: number;
}

interface ArchitectureData {
  components: ComponentItem[];
  relationships: RelationshipItem[];
  layers: Record<string, string[]>;
  mermaid_diagram: string;
  layer_diagram: string;
  summary: {
    total_components: number;
    total_relationships: number;
    active_layer_count: number;
    layer_distribution: Record<string, number>;
  };
}

const LAYER_META: Record<string, { label: string; color: string }> = {
  api: { label: "API", color: "bg-blue-100 text-blue-800 border-blue-300" },
  controller: { label: "Controller", color: "bg-purple-100 text-purple-800 border-purple-300" },
  service: { label: "Service", color: "bg-emerald-100 text-emerald-800 border-emerald-300" },
  repository: { label: "Repository", color: "bg-amber-100 text-amber-800 border-amber-300" },
  database: { label: "Database", color: "bg-rose-100 text-rose-800 border-rose-300" },
  external_service: { label: "External", color: "bg-cyan-100 text-cyan-800 border-cyan-300" },
  frontend: { label: "Frontend", color: "bg-indigo-100 text-indigo-800 border-indigo-300" },
  utility: { label: "Utility", color: "bg-gray-100 text-gray-800 border-gray-300" },
};

export default function ArchitectureClient({ repoId }: { repoId: string }) {
  const [data, setData] = useState<ArchitectureData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterLayer, setFilterLayer] = useState<string>("all");
  const [selectedComponent, setSelectedComponent] = useState<ComponentItem | null>(null);
  const [diagramMode, setDiagramMode] = useState<"component" | "layer">("component");
  const [copied, setCopied] = useState(false);

  const fetchArchitecture = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/repos/${repoId}/architecture`);
      if (!res.ok) {
        if (res.status === 404) {
          setError("Architecture data not found. Please ingest the repository to generate static graphs.");
        } else {
          setError("Failed to fetch architecture intelligence.");
        }
        return;
      }
      const json: ArchitectureData = await res.json();
      setData(json);
      if (json.components && json.components.length > 0) {
        setSelectedComponent(json.components[0]);
      }
    } catch (err) {
      setError("Unable to connect to RepoSense backend API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchArchitecture();
  }, [repoId]);

  const activeDiagram = diagramMode === "component" ? data?.mermaid_diagram : data?.layer_diagram;

  const handleCopyMermaid = () => {
    if (activeDiagram) {
      navigator.clipboard.writeText(activeDiagram);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExportMermaid = () => {
    if (activeDiagram) {
      const blob = new Blob([activeDiagram], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${repoId}_architecture_${diagramMode}.mmd`;
      link.click();
      URL.revokeObjectURL(url);
    }
  };

  const filteredComponents = data?.components.filter(
    (c) => filterLayer === "all" || c.role === filterLayer
  ) || [];

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header Card */}
      <div className="border border-gh-border rounded-md bg-white">
        <div className="bg-gh-bg border-b border-gh-border px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Network size={16} className="text-[#0969da]" />
            <h2 className="font-semibold text-sm text-gh-text">Architecture Intelligence & Flow Diagrams</h2>
          </div>
          <div className="flex gap-2">
            <button
              onClick={handleCopyMermaid}
              className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 border border-gh-border rounded-md bg-white hover:bg-gray-50 text-gh-text"
              title="Copy Mermaid diagram source"
            >
              {copied ? <Check size={12} className="text-emerald-600" /> : <Copy size={12} />}
              {copied ? "Copied" : "Copy Mermaid"}
            </button>
            <button
              onClick={handleExportMermaid}
              className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 border border-gh-border rounded-md bg-white hover:bg-gray-50 text-gh-text"
              title="Export Mermaid file"
            >
              <Download size={12} /> Export
            </button>
            <button
              onClick={fetchArchitecture}
              className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 border border-gh-border rounded-md bg-white hover:bg-gray-50 text-gh-text"
            >
              <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
            </button>
          </div>
        </div>

        {/* Layer Metrics Row */}
        {data && (
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 border-b border-gh-border divide-x divide-gh-border text-center">
            {Object.entries(data.summary.layer_distribution).map(([role, count]) => {
              const meta = LAYER_META[role] || { label: role, color: "bg-gray-100" };
              return (
                <div key={role} className="p-3">
                  <span className="text-[11px] font-semibold text-gh-text-secondary uppercase">{meta.label}</span>
                  <div className="text-lg font-bold text-gh-text mt-0.5">{count}</div>
                </div>
              );
            })}
          </div>
        )}

        {/* Filter Navigation */}
        {data && (
          <div className="p-3 flex flex-wrap gap-2 items-center bg-gray-50/50">
            <span className="text-xs font-semibold text-gh-text-secondary mr-2">Filter Layers:</span>
            <button
              onClick={() => setFilterLayer("all")}
              className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                filterLayer === "all"
                  ? "bg-[#0969da] text-white"
                  : "bg-white border border-gh-border text-gh-text hover:bg-gray-100"
              }`}
            >
              All Components ({data.components.length})
            </button>
            {Object.entries(data.summary.layer_distribution).map(([role, count]) => {
              const meta = LAYER_META[role] || { label: role };
              return (
                <button
                  key={role}
                  onClick={() => setFilterLayer(role)}
                  className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                    filterLayer === role
                      ? "bg-[#0969da] text-white"
                      : "bg-white border border-gh-border text-gh-text hover:bg-gray-100"
                  }`}
                >
                  {meta.label} ({count})
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Main Content Area */}
      {loading ? (
        <div className="border border-gh-border rounded-md bg-white p-16 flex flex-col items-center justify-center text-gh-text-secondary">
          <div className="w-8 h-8 border-4 border-[#0969da] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-sm font-semibold text-gh-text">Analyzing architectural relationships...</p>
        </div>
      ) : error ? (
        <div className="border border-gh-border rounded-md bg-white p-12 flex flex-col items-center justify-center text-center">
          <AlertCircle size={32} className="text-amber-500 mb-3" />
          <p className="text-sm font-semibold text-gh-text">{error}</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Component List */}
          <div className="border border-gh-border rounded-md bg-white overflow-hidden flex flex-col">
            <div className="bg-gh-bg border-b border-gh-border px-4 py-2.5 flex justify-between items-center">
              <span className="font-semibold text-xs uppercase tracking-wider text-gh-text-secondary">
                Components ({filteredComponents.length})
              </span>
            </div>
            <div className="max-h-[550px] overflow-y-auto divide-y divide-gh-border">
              {filteredComponents.map((comp) => {
                const meta = LAYER_META[comp.role] || { label: comp.role, color: "bg-gray-100 text-gray-800" };
                const isSelected = selectedComponent?.id === comp.id;
                return (
                  <div
                    key={comp.id}
                    onClick={() => setSelectedComponent(comp)}
                    className={`p-3 cursor-pointer transition-colors flex items-center justify-between text-sm ${
                      isSelected ? "bg-blue-50/70 border-l-4 border-l-[#0969da]" : "hover:bg-gray-50"
                    }`}
                  >
                    <div className="min-w-0 pr-2">
                      <div className="font-mono font-semibold text-gh-text text-xs truncate">{comp.name}</div>
                      {comp.file && (
                        <div className="text-[11px] font-mono text-gh-text-secondary truncate mt-0.5">
                          {comp.file}{comp.start_line ? `:${comp.start_line}` : ""}
                        </div>
                      )}
                    </div>
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase shrink-0 ${meta.color}`}>
                      {meta.label}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right Columns: Diagram & Component Detail */}
          <div className="lg:col-span-2 flex flex-col gap-6">
            {/* Mermaid Diagram Box */}
            <div className="border border-gh-border rounded-md bg-white overflow-hidden flex flex-col">
              <div className="bg-gh-bg border-b border-gh-border px-4 py-2 flex justify-between items-center">
                <div className="flex gap-2">
                  <button
                    onClick={() => setDiagramMode("component")}
                    className={`text-xs px-2.5 py-1 rounded-md font-semibold transition-colors ${
                      diagramMode === "component" ? "bg-white shadow-sm border border-gh-border text-gh-text" : "text-gh-text-secondary hover:text-gh-text"
                    }`}
                  >
                    Component Flow
                  </button>
                  <button
                    onClick={() => setDiagramMode("layer")}
                    className={`text-xs px-2.5 py-1 rounded-md font-semibold transition-colors ${
                      diagramMode === "layer" ? "bg-white shadow-sm border border-gh-border text-gh-text" : "text-gh-text-secondary hover:text-gh-text"
                    }`}
                  >
                    Layer Interactions
                  </button>
                </div>
                <span className="text-[11px] font-mono text-gh-text-secondary">Evidence-backed Mermaid</span>
              </div>
              <div className="p-4 bg-gray-50/70 overflow-x-auto max-h-[320px]">
                <pre className="font-mono text-xs text-gh-text whitespace-pre leading-relaxed">
                  {activeDiagram}
                </pre>
              </div>
            </div>

            {/* Selected Component Inspection Panel */}
            {selectedComponent && (
              <div className="border border-gh-border rounded-md bg-white p-5 flex flex-col gap-3">
                <div className="flex items-center justify-between border-b border-gh-border pb-3">
                  <div>
                    <span className="text-[10px] font-mono font-semibold uppercase px-2 py-0.5 rounded bg-gray-100 text-gh-text-secondary border border-gh-border">
                      {selectedComponent.role}
                    </span>
                    <h3 className="font-mono font-bold text-sm text-gh-text mt-1">{selectedComponent.name}</h3>
                  </div>
                  {selectedComponent.file && (
                    <div className="text-right">
                      <span className="text-xs font-mono text-gh-text-secondary">
                        {selectedComponent.file}:{selectedComponent.start_line}-{selectedComponent.end_line}
                      </span>
                    </div>
                  )}
                </div>

                {selectedComponent.docstring && (
                  <div className="text-xs text-gh-text bg-gray-50 p-3 rounded-md border border-gh-border">
                    <span className="font-semibold text-gh-text-secondary block mb-1">Docstring / Documentation:</span>
                    {selectedComponent.docstring}
                  </div>
                )}

                <div>
                  <h4 className="text-xs font-semibold text-gh-text-secondary uppercase mb-2">
                    Verified Outgoing Calls ({selectedComponent.outgoing_calls.length})
                  </h4>
                  {selectedComponent.outgoing_calls.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {selectedComponent.outgoing_calls.map((call, idx) => (
                        <span key={idx} className="text-xs font-mono px-2 py-1 rounded bg-blue-50 border border-blue-200 text-[#0969da]">
                          &rarr; {call}
                        </span>
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-gh-text-secondary italic">No outgoing calls from this component.</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
