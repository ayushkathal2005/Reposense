import React, { Suspense } from "react";
import ArchitectureClient from "./ArchitectureClient";

async function ArchitectureContent({ params }: { params: Promise<{ id: string }> }) {
  const { id: repoId } = await params;
  return <ArchitectureClient repoId={repoId} />;
}

export default function ArchitecturePage({ params }: { params: Promise<{ id: string }> }) {
  return (
    <Suspense fallback={<div className="p-8 text-center text-gh-text-secondary">Loading architecture graph...</div>}>
      <ArchitectureContent params={params} />
    </Suspense>
  );
}
