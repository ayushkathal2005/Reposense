import { Settings } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="flex gap-6">
      <div className="w-64 flex-shrink-0">
        <nav className="flex flex-col gap-1">
          <a href="#" className="px-3 py-1.5 text-sm font-semibold bg-gray-100 rounded-md border-l-4 border-[#fd8c73] text-gh-text">General</a>
          <a href="#" className="px-3 py-1.5 text-sm text-gh-text-secondary hover:bg-gray-50 rounded-md">Collaborators</a>
          <a href="#" className="px-3 py-1.5 text-sm text-gh-text-secondary hover:bg-gray-50 rounded-md">Webhooks</a>
          <a href="#" className="px-3 py-1.5 text-sm text-gh-text-secondary hover:bg-gray-50 rounded-md">Environments</a>
          <a href="#" className="px-3 py-1.5 text-sm text-gh-text-secondary hover:bg-gray-50 rounded-md">RepoSense Intelligence</a>
        </nav>
      </div>
      <div className="flex-1">
        <h2 className="text-xl font-semibold mb-4 border-b border-gh-border pb-2">Settings</h2>
        
        <div className="mb-8">
          <h3 className="font-semibold mb-2">Repository name</h3>
          <input type="text" defaultValue="repository" className="w-full max-w-sm px-3 py-1.5 text-sm border border-gh-border rounded-md" />
          <button className="ml-2 bg-gh-btn-bg border border-gh-border hover:bg-gh-btn-hover font-semibold py-1.5 px-4 rounded-md text-sm transition-colors">Rename</button>
        </div>

        <div className="border border-red-300 rounded-md overflow-hidden">
          <div className="bg-red-50 border-b border-red-300 px-4 py-3 font-semibold text-red-700">Danger Zone</div>
          <div className="p-4 bg-white flex justify-between items-center">
            <div>
              <div className="font-semibold text-sm">Delete this repository</div>
              <div className="text-sm text-gh-text-secondary">Once you delete a repository, there is no going back. Please be certain.</div>
            </div>
            <button className="bg-white border border-red-300 hover:bg-red-700 hover:text-white text-red-700 font-semibold py-1.5 px-4 rounded-md text-sm transition-colors">Delete repository</button>
          </div>
        </div>
      </div>
    </div>
  );
}
