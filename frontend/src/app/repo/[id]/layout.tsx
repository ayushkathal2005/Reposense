import React, { ReactNode, Suspense } from "react";
import { BookOpen, Star, GitFork } from "lucide-react";
import RepoTabs from "./RepoTabs";

export default function RepoLayout({
  children,
}: {
  children: ReactNode;
}) {

  return (
    <div className="flex-1 flex flex-col min-h-screen bg-gh-bg">
      <div className="bg-white border-b border-gh-border pt-4 px-4 sm:px-6">
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center gap-2 text-xl">
            <BookOpen size={20} className="text-gh-text-secondary" />
            <span className="text-[#0969da] hover:underline cursor-pointer">owner</span>
            <span className="text-gh-text-secondary font-normal">/</span>
            <span className="text-[#0969da] hover:underline cursor-pointer font-semibold">repository</span>
            <span className="px-2 py-0.5 border border-gh-border rounded-full text-xs text-gh-text-secondary ml-2 font-medium">Public</span>
          </div>
          
          <div className="flex items-center gap-2 text-xs">
            <button className="flex items-center gap-1.5 border border-gh-border bg-gh-btn-bg hover:bg-gh-btn-hover px-3 py-1 rounded-md font-semibold text-gh-text">
              <Star size={14} /> Star <span className="ml-1 bg-white border border-gh-border px-1.5 rounded-full">0</span>
            </button>
            <button className="flex items-center gap-1.5 border border-gh-border bg-gh-btn-bg hover:bg-gh-btn-hover px-3 py-1 rounded-md font-semibold text-gh-text">
              <GitFork size={14} /> Fork <span className="ml-1 bg-white border border-gh-border px-1.5 rounded-full">0</span>
            </button>
          </div>
        </div>

        <Suspense fallback={<div className="h-10 mt-4"></div>}>
          <RepoTabs />
        </Suspense>
      </div>
      
      <div className="flex-1 max-w-7xl w-full mx-auto p-4 sm:p-6">
        {children}
      </div>
    </div>
  );
}
