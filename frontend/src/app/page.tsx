"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Book, CheckCircle, AlertCircle, Loader2 } from "lucide-react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");
  const router = useRouter();

  const handleIngest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;
    
    setStatus("loading");
    setMessage("Connecting to repository...");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/repos/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url })
      });
      
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      
      pollStatus(data.repo_id);
    } catch (err: any) {
      setStatus("error");
      setMessage(err.message || "Failed to connect to repository");
    }
  };

  const pollStatus = async (repoId: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/api/repos/${repoId}/status`);
      const data = await res.json();
      
      if (data.status === "completed") {
        setStatus("success");
        setMessage("Repository successfully indexed. Redirecting...");
        setTimeout(() => {
          router.push(`/repo/${repoId}`);
        }, 1000);
      } else if (data.status === "failed") {
        setStatus("error");
        setMessage("Failed to index repository.");
      } else {
        setMessage("Indexing repository and building Knowledge Graph...");
        setTimeout(() => pollStatus(repoId), 2000);
      }
    } catch (err: any) {
      setStatus("error");
      setMessage("Error checking status.");
    }
  };

  return (
    <div className="flex-1 flex flex-col items-center pt-16 px-4 bg-gh-bg">
      <div className="w-full max-w-[800px]">
        <div className="text-center mb-10">
          <h1 className="text-3xl font-semibold mb-2">Connect Repository to RepoSense</h1>
          <p className="text-gh-text-secondary">Analyze any codebase instantly with intelligent semantic search.</p>
        </div>

        <div className="bg-white border border-gh-border rounded-md shadow-sm">
          <div className="bg-gh-bg border-b border-gh-border px-4 py-3 rounded-t-md">
            <h2 className="font-semibold text-sm">Import a repository</h2>
          </div>
          
          <div className="p-6">
            <form onSubmit={handleIngest} className="space-y-4">
              <div>
                <label className="block text-sm font-semibold mb-2">
                  Repository URL
                </label>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="https://github.com/owner/repo"
                  className="w-full px-3 py-1.5 text-sm border border-gh-border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={status === "loading" || status === "success"}
                />
                <p className="text-xs text-gh-text-secondary mt-2">
                  Please provide the full HTTP URL to a public GitHub repository.
                </p>
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  disabled={!url || status === "loading" || status === "success"}
                  className="bg-[#1f883d] hover:bg-[#1a7f37] text-white font-semibold py-1.5 px-4 rounded-md text-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {status === "loading" && <Loader2 size={16} className="animate-spin" />}
                  Import and analyze
                </button>
              </div>
            </form>

            {status !== "idle" && (
              <div className={`mt-6 p-4 rounded-md border text-sm flex items-start gap-3
                ${status === 'loading' ? 'bg-[#ddf4ff] border-[#54aeff] text-[#0969da]' : ''}
                ${status === 'success' ? 'bg-[#dafbe1] border-[#4ac26b] text-[#1a7f37]' : ''}
                ${status === 'error' ? 'bg-[#ffebe9] border-[#ff8182] text-[#cf222e]' : ''}
              `}>
                {status === 'loading' && <Loader2 size={18} className="animate-spin mt-0.5" />}
                {status === 'success' && <CheckCircle size={18} className="mt-0.5" />}
                {status === 'error' && <AlertCircle size={18} className="mt-0.5" />}
                <div>
                  <div className="font-semibold">{message}</div>
                  {status === 'loading' && <div className="text-xs opacity-80 mt-1">This may take a minute depending on the size of the repository.</div>}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
