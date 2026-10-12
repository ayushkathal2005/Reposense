"use client";

import React, { useState } from "react";
import { Folder, FileText, Search, CornerDownRight, Check, Copy, ExternalLink, Box, Terminal } from "lucide-react";

export default function RepoCodePageClient({ repoId }: { repoId: string }) {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<{ answer: string; sources: any[]; prompt: string } | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setResult(null);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo_id: repoId, query }),
      });

      if (!res.ok) throw new Error("Failed to query the repository");

      const data = await res.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      alert("An error occurred while querying the repository.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex gap-6 h-[calc(100vh-140px)]">
      {/* Sidebar: File Explorer */}
      <div className="w-72 flex-shrink-0 flex flex-col bg-white border border-gh-border rounded-md overflow-hidden">
        <div className="bg-gh-bg border-b border-gh-border px-4 py-2.5 flex justify-between items-center">
          <span className="font-semibold text-sm text-gh-text flex items-center gap-2">
            <span className="text-gh-text-secondary font-normal">main</span>
          </span>
          <button className="text-xs font-semibold bg-white border border-gh-border px-2 py-0.5 rounded-md text-gh-text">Branches</button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-2">
          <div className="text-xs font-semibold text-gh-text-secondary px-2 mb-2 mt-2">Files</div>
          <div className="flex flex-col">
            {[
              { name: "src", type: "folder" },
              { name: "public", type: "folder" },
              { name: "package.json", type: "file" },
              { name: "README.md", type: "file" },
              { name: "next.config.js", type: "file" },
              { name: "tailwind.config.js", type: "file" },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center gap-2 px-2 py-1.5 hover:bg-gray-100 rounded-md cursor-pointer group">
                {item.type === "folder" ? (
                  <Folder size={16} className="text-[#54aeff] fill-[#54aeff]/20" />
                ) : (
                  <FileText size={16} className="text-gh-text-secondary" />
                )}
                <span className="text-sm text-gh-text group-hover:text-[#0969da] truncate">{item.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        
        {/* Search / AI Query Box */}
        <div className="mb-4">
          <form onSubmit={handleSearch} className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search size={16} className="text-gh-text-secondary" />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask anything about this repository..."
              className="block w-full pl-10 pr-12 py-2 border border-gh-border rounded-md leading-5 bg-white placeholder-gh-text-secondary focus:outline-none focus:ring-2 focus:ring-[#0969da] focus:border-[#0969da] sm:text-sm text-gh-text transition-shadow shadow-sm"
              disabled={isLoading}
            />
            <div className="absolute inset-y-0 right-0 pr-2 flex items-center">
              <button 
                type="submit" 
                disabled={isLoading || !query.trim()}
                className="p-1 text-gh-text-secondary hover:text-gh-text disabled:opacity-50"
              >
                <CornerDownRight size={16} />
              </button>
            </div>
          </form>
        </div>

        {/* Results Area */}
        <div className="flex-1 border border-gh-border rounded-md bg-white overflow-hidden flex flex-col">
          {isLoading ? (
            <div className="flex-1 flex flex-col items-center justify-center p-12">
              <div className="w-8 h-8 border-4 border-[#0969da] border-t-transparent rounded-full animate-spin mb-4"></div>
              <h3 className="text-lg font-semibold text-gh-text">Analyzing codebase...</h3>
              <p className="text-sm text-gh-text-secondary mt-1 max-w-md text-center">
                RepoSense is reading the source code, resolving symbols, and generating an accurate response.
              </p>
            </div>
          ) : result ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="bg-gh-bg border-b border-gh-border px-4 py-3 flex justify-between items-center shrink-0">
                <h3 className="font-semibold text-sm text-gh-text flex items-center gap-2">
                  <Terminal size={16} /> Analysis Result
                </h3>
                <div className="flex gap-2">
                  <button className="p-1 hover:bg-gray-200 rounded text-gh-text-secondary" title="Copy result">
                    <Copy size={16} />
                  </button>
                </div>
              </div>
              
              <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-8">
                {/* Answer Section */}
                <div>
                  <div className="prose prose-sm max-w-none text-gh-text font-sans">
                    {result.answer.split('\n').map((line, i) => (
                      <p key={i} className="mb-2">{line}</p>
                    ))}
                  </div>
                </div>

                {/* Sources Section */}
                {result.sources && result.sources.length > 0 && (
                  <div className="border-t border-gh-border pt-6 mt-2">
                    <h4 className="text-xs font-semibold text-gh-text-secondary uppercase tracking-wider mb-4">Referenced Code</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {result.sources.map((source, idx) => (
                        <div key={idx} className="border border-gh-border rounded-md bg-gh-bg p-3 group hover:border-[#0969da] transition-colors cursor-pointer flex flex-col h-full">
                          <div className="flex items-center gap-2 mb-2 text-sm">
                            <Box size={14} className="text-[#0969da]" />
                            <span className="font-mono text-gh-text truncate font-semibold" title={source.name}>{source.name}</span>
                          </div>
                          <div className="text-xs font-mono text-gh-text-secondary truncate mt-auto">
                            {source.file_path || source.file}{source.lines ? `:${source.lines}` : ""}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-gh-text-secondary">
              <Search size={48} className="mb-4 text-gray-300" />
              <h3 className="text-lg font-semibold text-gh-text mb-2">Explore the Codebase</h3>
              <p className="text-sm max-w-md mx-auto">
                Search for any function, class, or architectural pattern. RepoSense uses deep code intelligence to provide accurate answers with context.
              </p>
              <div className="mt-8 flex flex-wrap gap-2 justify-center max-w-lg">
                {["Where is the database initialized?", "How does authentication work?", "Show me the routing logic"].map((q, i) => (
                  <button 
                    key={i}
                    onClick={() => setQuery(q)}
                    className="text-xs border border-gh-border bg-gh-bg hover:bg-gray-100 px-3 py-1.5 rounded-full text-gh-text-secondary transition-colors"
                  >
                    "{q}"
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
