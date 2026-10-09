import { GitPullRequest } from "lucide-react";

export default function PullsPage() {
  return (
    <div className="border border-gh-border rounded-md bg-white">
      <div className="bg-gh-bg border-b border-gh-border px-4 py-3">
        <h2 className="font-semibold text-sm">Pull requests</h2>
      </div>
      <div className="p-16 flex flex-col items-center justify-center text-gh-text-secondary min-h-[400px]">
        <GitPullRequest size={48} className="mb-4 opacity-20" />
        <h3 className="text-xl font-semibold text-gh-text mb-2">Welcome to pull requests!</h3>
        <p className="text-sm">Pull requests help you collaborate on code with other people.</p>
        <p className="text-sm mt-1">RepoSense AI impact analysis for PRs will be available here.</p>
      </div>
    </div>
  );
}
