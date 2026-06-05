"use client";

import dynamic from "next/dynamic";
import React from "react";

const MarkdownRendererInner = dynamic(
  () => import("@/components/ui/markdown-inner"),
  { ssr: false },
);

function MarkdownFallback() {
  return (
    <div
      className="skeleton"
      style={{ height: 40, width: "100%", borderRadius: 8, margin: "4px 0" }}
    />
  );
}

interface MarkdownRendererProps {
  content: string;
}

export function MarkdownRenderer({ content }: MarkdownRendererProps) {
  if (!content) return null;
  return (
    <React.Suspense fallback={<MarkdownFallback />}>
      <MarkdownRendererInner content={content} />
    </React.Suspense>
  );
}
