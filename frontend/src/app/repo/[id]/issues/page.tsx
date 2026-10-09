import { CircleDot } from "lucide-react";

export default function IssuesPage() {
  return (
    <div className="border border-gh-border rounded-md bg-white">
      <div className="bg-gh-bg border-b border-gh-border px-4 py-3">
        <h2 className="font-semibold text-sm">Issues</h2>
      </div>
      <div className="p-16 flex flex-col items-center justify-center text-gh-text-secondary min-h-[400px]">
        <CircleDot size={48} className="mb-4 opacity-20" />
        <h3 className="text-xl font-semibold text-gh-text mb-2">Welcome to issues!</h3>
        <p className="text-sm">Issues are used to track todos, bugs, feature requests, and more.</p>
        <p className="text-sm mt-1">RepoSense intelligence analysis of issues is coming soon.</p>
      </div>
    </div>
  );
}
