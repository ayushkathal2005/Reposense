import React, { Suspense } from "react";
import RepoCodePageClient from "./RepoCodePageClient";

export const dynamic = "force-dynamic";

export default async function RepoCodePage({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading code intelligence...</div>}>
      <RepoCodePageClient repoId={repoId} />
    </Suspense>
  );
}
