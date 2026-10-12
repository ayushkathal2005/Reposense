import React, { Suspense } from "react";
import DocsClient from "./DocsClient";

async function DocsContent({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return <DocsClient repoId={repoId} />;
}

export default function DocsPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading Repository Documentation Engine...</div>}>
      <DocsContent params={params} />
    </Suspense>
  );
}
