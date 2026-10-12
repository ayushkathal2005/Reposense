import React, { Suspense } from "react";
import DependenciesClient from "./DependenciesClient";

async function DependenciesContent({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return <DependenciesClient repoId={repoId} />;
}

export default function DependenciesPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading Repository Dependencies...</div>}>
      <DependenciesContent params={params} />
    </Suspense>
  );
}
