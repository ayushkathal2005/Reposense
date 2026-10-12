import React, { Suspense } from "react";
import DebugClient from "./DebugClient";

async function DebugContent({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return <DebugClient repoId={repoId} />;
}

export default function DebugPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading Repository-Aware Debugger...</div>}>
      <DebugContent params={params} />
    </Suspense>
  );
}
