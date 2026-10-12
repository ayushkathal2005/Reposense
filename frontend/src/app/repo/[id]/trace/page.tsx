import React, { Suspense } from "react";
import TraceClient from "./TraceClient";

async function TraceContent({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return <TraceClient repoId={repoId} />;
}

export default function TracePage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading Execution Flow Tracer...</div>}>
      <TraceContent params={params} />
    </Suspense>
  );
}
