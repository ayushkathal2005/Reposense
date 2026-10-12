import React, { Suspense } from "react";
import RepoCodePageClient from "./RepoCodePageClient";

async function RepoCodeContent({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return <RepoCodePageClient repoId={repoId} />;
}

export default function RepoCodePage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading code intelligence...</div>}>
      <RepoCodeContent params={params} />
    </Suspense>
  );
}
