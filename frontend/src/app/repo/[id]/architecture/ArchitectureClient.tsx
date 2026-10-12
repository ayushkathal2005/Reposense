"use client";

import React, { useEffect, useState } from "react";
import { Network, Box, FileText, Share2, Layers, AlertCircle, RefreshCw } from "lucide-react";

interface NodeItem {
  id: string;
  name: string;
  type: string;
  file?: string;
  start_line?: number;
  end_line?: number;
}

interface EdgeItem {
  source: string;
  target: string;
  relationship: string;
}

interface GraphData {
  node_count: number;
  edge_count: number;
  node_types: Record<string, number>;
  nodes: NodeItem[];
  edges: EdgeItem[];
}

export default function ArchitectureClient({ repoId }: { repoId: string }) {
  const [data, setData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>("all");

  const fetchGraph = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/repos/${repoId}/graph`);
      if (!res.ok) {
        if (res.status === 404) {
          setError("Knowledge graph not yet generated for this repository. Please run ingestion first.");
        } else {
          setError("Failed to fetch repository knowledge graph.");
        }
        return;
      }
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError("Unable to connect to RepoSense backend API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [repoId]);

  const filteredNodes = data?.nodes.filter((n) => filterType === "all" || n.type === filterType) || [];

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header Card */}
      <div className="border border-gh-border rounded-md bg-white">
        <div className="bg-gh-bg border-b border-gh-border px-4 py-3 flex justify-between items-center">
          <div className="flex items-center gap-2">
            <Network size={16} className="text-[#0969da]" />
            <h2 className="font-semibold text-sm text-gh-text">Persistent Knowledge Graph</h2>
          </div>
          <button
            onClick={fetchGraph}
            className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 border border-gh-border rounded-md bg-white hover:bg-gray-50 text-gh-text"
          >
            <RefreshCw size={12} className={loading ? "animate-spin" : ""} /> Refresh
          </button>
        </div>

        {/* Stats Row */}
        {data && (
          <div className="grid grid-cols-2 sm:grid-cols-4 border-b border-gh-border divide-x divide-gh-border">
            <div className="p-4">
              <span className="text-xs font-semibold text-gh-text-secondary uppercase">Total Nodes</span>
              <div className="text-xl font-bold text-gh-text mt-1">{data.node_count}</div>
            </div>
            <div className="p-4">
              <span className="text-xs font-semibold text-gh-text-secondary uppercase">Relationships</span>
              <div className="text-xl font-bold text-gh-text mt-1">{data.edge_count}</div>
            </div>
            <div className="p-4">
              <span className="text-xs font-semibold text-gh-text-secondary uppercase">Component Types</span>
              <div className="text-xl font-bold text-gh-text mt-1">{Object.keys(data.node_types).length}</div>
            </div>
            <div className="p-4">
              <span className="text-xs font-semibold text-gh-text-secondary uppercase">Storage</span>
              <div className="text-xl font-bold text-emerald-600 mt-1">Indexed & Cached</div>
            </div>
          </div>
        )}

        {/* Filter Pills */}
        {data && (
          <div className="p-4 flex flex-wrap gap-2 items-center bg-gray-50/50">
            <span className="text-xs font-semibold text-gh-text-secondary mr-2">Filter by Type:</span>
            <button
              onClick={() => setFilterType("all")}
              className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                filterType === "all"
                  ? "bg-[#0969da] text-white"
                  : "bg-white border border-gh-border text-gh-text hover:bg-gray-100"
              }`}
            >
              All ({data.nodes.length})
            </button>
            {Object.entries(data.node_types).map(([type, count]) => (
              <button
                key={type}
                onClick={() => setFilterType(type)}
                className={`text-xs px-2.5 py-1 rounded-full font-medium transition-colors ${
                  filterType === type
                    ? "bg-[#0969da] text-white"
                    : "bg-white border border-gh-border text-gh-text hover:bg-gray-100"
                }`}
              >
                {type} ({count})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Main Content / Table */}
      {loading ? (
        <div className="border border-gh-border rounded-md bg-white p-16 flex flex-col items-center justify-center text-gh-text-secondary">
          <div className="w-8 h-8 border-4 border-[#0969da] border-t-transparent rounded-full animate-spin mb-4" />
          <p className="text-sm font-semibold text-gh-text">Loading persistent graph relationships...</p>
        </div>
      ) : error ? (
        <div className="border border-gh-border rounded-md bg-white p-12 flex flex-col items-center justify-center text-center">
          <AlertCircle size={32} className="text-amber-500 mb-3" />
          <p className="text-sm font-semibold text-gh-text">{error}</p>
          <p className="text-xs text-gh-text-secondary mt-1 max-w-sm">
            Ingest a repository via the main dashboard or terminal to automatically build and persist the knowledge graph.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Nodes Table */}
          <div className="lg:col-span-2 border border-gh-border rounded-md bg-white overflow-hidden">
            <div className="bg-gh-bg border-b border-gh-border px-4 py-2.5 flex justify-between items-center">
              <span className="font-semibold text-xs uppercase tracking-wider text-gh-text-secondary">
                Components & Symbols ({filteredNodes.length})
              </span>
            </div>
            <div className="max-h-[500px] overflow-y-auto divide-y divide-gh-border">
              {filteredNodes.map((node) => (
                <div key={node.id} className="p-3 hover:bg-gray-50 flex items-center justify-between text-sm">
                  <div className="flex items-center gap-2.5 min-w-0">
                    {node.type === "file" ? (
                      <FileText size={16} className="text-gh-text-secondary shrink-0" />
                    ) : node.type === "repository" ? (
                      <Layers size={16} className="text-[#0969da] shrink-0" />
                    ) : (
                      <Box size={16} className="text-purple-600 shrink-0" />
                    )}
                    <div className="truncate">
                      <div className="font-mono font-semibold text-gh-text text-xs truncate">{node.name}</div>
                      {node.file && (
                        <div className="text-[11px] font-mono text-gh-text-secondary truncate">
                          {node.file}
                          {node.start_line ? `:${node.start_line}-${node.end_line}` : ""}
                        </div>
                      )}
                    </div>
                  </div>
                  <span className="text-[11px] font-mono font-semibold px-2 py-0.5 rounded bg-gray-100 text-gh-text-secondary border border-gh-border shrink-0 ml-2">
                    {node.type}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Relationships Stream */}
          <div className="border border-gh-border rounded-md bg-white overflow-hidden flex flex-col">
            <div className="bg-gh-bg border-b border-gh-border px-4 py-2.5 flex justify-between items-center">
              <span className="font-semibold text-xs uppercase tracking-wider text-gh-text-secondary flex items-center gap-1.5">
                <Share2 size={13} /> Relationships ({data?.edges.length || 0})
              </span>
            </div>
            <div className="max-h-[500px] overflow-y-auto divide-y divide-gh-border p-2">
              {data?.edges.map((edge, idx) => (
                <div key={idx} className="p-2 text-xs font-mono flex flex-col gap-1">
                  <div className="flex items-center justify-between text-gh-text">
                    <span className="truncate max-w-[120px] font-semibold" title={edge.source}>{edge.source}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-50 text-[#0969da] border border-blue-200 uppercase font-semibold">
                      {edge.relationship}
                    </span>
                    <span className="truncate max-w-[120px] text-gh-text-secondary" title={edge.target}>{edge.target}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
