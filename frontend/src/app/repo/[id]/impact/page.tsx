import React, { Suspense } from "react";
import ImpactClient from "./ImpactClient";

async function ImpactContent({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return <ImpactClient repoId={repoId} />;
}

export default function ImpactPage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading Change Impact Analyzer...</div>}>
      <ImpactContent params={params} />
    </Suspense>
  );
}
