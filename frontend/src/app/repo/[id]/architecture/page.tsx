import { Network } from "lucide-react";

export default function ArchitecturePage() {
  return (
    <div className="border border-gh-border rounded-md bg-white">
      <div className="bg-gh-bg border-b border-gh-border px-4 py-3 flex justify-between items-center">
        <h2 className="font-semibold text-sm flex items-center gap-2">
          <Network size={16} /> Architecture Diagram
        </h2>
        <div className="flex gap-2">
          <button className="text-xs font-semibold px-3 py-1 border border-gh-border rounded-md bg-white hover:bg-gray-50">Filter</button>
          <button className="text-xs font-semibold px-3 py-1 border border-gh-border rounded-md bg-white hover:bg-gray-50">Export</button>
        </div>
      </div>
      <div className="p-16 flex flex-col items-center justify-center text-gh-text-secondary min-h-[400px]">
        <Network size={48} className="mb-4 opacity-20" />
        <p className="text-sm">Architecture graph generation is currently in beta.</p>
        <p className="text-sm mt-1">Please use the Code tab to query the repository intelligence.</p>
      </div>
    </div>
  );
}
