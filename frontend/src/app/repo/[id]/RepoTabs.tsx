"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { Code, GitPullRequest, CircleDot, Activity, GitCommit, Boxes, Zap, Bug, BookOpen, Settings } from "lucide-react";

export default function RepoTabs() {
  const pathname = usePathname();
  const params = useParams();
  const repoId = params.id as string;
  const tabs = [
    { name: "Code", href: `/repo/${repoId}`, icon: Code },
    { name: "Architecture", href: `/repo/${repoId}/architecture`, icon: Activity },
    { name: "Execution Flow", href: `/repo/${repoId}/trace`, icon: GitCommit },
    { name: "Dependencies", href: `/repo/${repoId}/dependencies`, icon: Boxes },
    { name: "Impact", href: `/repo/${repoId}/impact`, icon: Zap },
    { name: "Debug", href: `/repo/${repoId}/debug`, icon: Bug },
    { name: "Docs", href: `/repo/${repoId}/docs`, icon: BookOpen },
    { name: "Settings", href: `/repo/${repoId}/settings`, icon: Settings },
  ];

  return (
    <nav className="flex gap-2 mt-4">
      {tabs.map((tab) => {
        const isActive = pathname === tab.href;
        const Icon = tab.icon;
        return (
          <Link
            key={tab.name}
            href={tab.href}
            className={`flex items-center gap-2 px-3 py-2 text-sm font-medium rounded-t-md border-b-2 transition-colors ${
              isActive
                ? "border-[#fd8c73] text-gh-text font-semibold"
                : "border-transparent text-gh-text-secondary hover:bg-gray-100 hover:text-gh-text"
            }`}
          >
            <Icon size={16} className={isActive ? "text-gh-text" : "text-gh-text-secondary"} />
            {tab.name}
          </Link>
        );
      })}
    </nav>
  );
}
