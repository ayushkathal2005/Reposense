"use client";

import React, { useEffect, useState } from "react";
import {
  Boxes,
  Network,
  Search,
  RefreshCw,
  GitPullRequest,
  FileCode,
  ArrowUpRight,
  ArrowDownLeft,
  Filter
} from "lucide-react";

interface GraphInspection {
  total_nodes: number;
  total_edges: number;
  density: number;
  top_in_degree: Array<{ node: string; in_degree: number; type?: string; file?: string }>;
  top_out_degree: Array<{ node: string; out_degree: number; type?: string; file?: string }>;
}

export default function DependenciesClient({ repoId }: { repoId: string }) {
  const [data, setData] = useState<GraphInspection | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterQuery, setFilterQuery] = useState("");

  const fetchGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://localhost:8000/api/repos/${repoId}/graph`);
      if (!res.ok) {
        throw new Error(`Failed to load dependency graph (status ${res.status})`);
      }
      const json: GraphInspection = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "Failed to load dependency graph");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [repoId]);

  return (
    <div className="flex flex-col gap-6 p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="border-b border-gh-border pb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-md bg-teal-500/10 text-teal-600 border border-teal-500/20">
            <Boxes size={22} />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gh-text">Dependency Inspector</h1>
            <p className="text-sm text-gh-text-secondary">
              Persistent Knowledge Graph inspection of inter-symbol connections, fan-in callers, and fan-out callees.
            </p>
          </div>
        </div>

        <button
          onClick={fetchGraph}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium border border-gh-border rounded-md hover:bg-gray-50 text-gh-text transition-colors self-start sm:self-auto"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Loading state */}
      {loading && (
        <div className="p-12 text-center text-gh-text-secondary flex flex-col items-center gap-3">
          <RefreshCw className="animate-spin text-blue-600" size={24} />
          <p className="text-sm">Inspecting repository dependency graph...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Main Content */}
      {data && !loading && (
        <div className="space-y-6">
          {/* Summary KPI Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="bg-gh-bg border border-gh-border rounded-lg p-4 shadow-sm">
              <span className="text-xs uppercase font-semibold text-gh-text-secondary">Indexed Nodes</span>
              <div className="text-2xl font-bold font-mono text-gh-text mt-1">{data.total_nodes}</div>
              <p className="text-xs text-gh-text-secondary mt-0.5">Classes, functions, routes, and files</p>
            </div>

            <div className="bg-gh-bg border border-gh-border rounded-lg p-4 shadow-sm">
              <span className="text-xs uppercase font-semibold text-gh-text-secondary">Dependency Edges</span>
              <div className="text-2xl font-bold font-mono text-gh-text mt-1">{data.total_edges}</div>
              <p className="text-xs text-gh-text-secondary mt-0.5">Calls, inherits, and depends_on edges</p>
            </div>

            <div className="bg-gh-bg border border-gh-border rounded-lg p-4 shadow-sm">
              <span className="text-xs uppercase font-semibold text-gh-text-secondary">Graph Density</span>
              <div className="text-2xl font-bold font-mono text-gh-text mt-1">{(data.density * 100).toFixed(2)}%</div>
              <p className="text-xs text-gh-text-secondary mt-0.5">Coupling connectivity ratio</p>
            </div>
          </div>

          {/* Top In-Degree & Top Out-Degree Tables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Highest Fan-In (Core Components) */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gh-text flex items-center gap-2">
                  <ArrowDownLeft size={16} className="text-emerald-500" />
                  <span>Highest Fan-In (Core Shared Symbols)</span>
                </h3>
                <span className="text-xs text-gh-text-secondary font-mono">Incoming Callers</span>
              </div>

              <div className="divide-y divide-gh-border border border-gh-border rounded-md overflow-hidden">
                {data.top_in_degree.slice(0, 8).map((item, idx) => (
                  <div key={idx} className="p-3 bg-gh-bg hover:bg-gray-50 flex items-center justify-between text-xs font-mono">
                    <div className="space-y-0.5">
                      <span className="font-semibold text-gh-text">{item.node}</span>
                      {item.file && (
                        <div className="text-[11px] text-gh-text-secondary">{item.file}</div>
                      )}
                    </div>
                    <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold shrink-0">
                      {item.in_degree} callers
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Highest Fan-Out (Complex Orchestrators) */}
            <div className="bg-gh-bg border border-gh-border rounded-lg p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-gh-text flex items-center gap-2">
                  <ArrowUpRight size={16} className="text-purple-500" />
                  <span>Highest Fan-Out (Orchestrators)</span>
                </h3>
                <span className="text-xs text-gh-text-secondary font-mono">Outgoing Calls</span>
              </div>

              <div className="divide-y divide-gh-border border border-gh-border rounded-md overflow-hidden">
                {data.top_out_degree.slice(0, 8).map((item, idx) => (
                  <div key={idx} className="p-3 bg-gh-bg hover:bg-gray-50 flex items-center justify-between text-xs font-mono">
                    <div className="space-y-0.5">
                      <span className="font-semibold text-gh-text">{item.node}</span>
                      {item.file && (
                        <div className="text-[11px] text-gh-text-secondary">{item.file}</div>
                      )}
                    </div>
                    <span className="px-2 py-0.5 rounded bg-purple-50 text-purple-700 border border-purple-200 font-bold shrink-0">
                      {item.out_degree} callees
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
