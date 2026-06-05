"use client";

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({
  width = "100%",
  height = 16,
  borderRadius,
  className = "",
  style,
}: SkeletonProps) {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius: borderRadius ?? "var(--radius-sm)",
        ...style,
      }}
    />
  );
}

export function MessageSkeleton() {
  return (
    <div className="chat-message flex items-start gap-3 px-4 py-3">
      <div
        className="skeleton w-8 h-8 rounded-lg shrink-0"
        style={{ borderRadius: 8 }}
      />
      <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 8 }}>
        <Skeleton width="60%" height={14} />
        <Skeleton width="90%" height={14} />
        <Skeleton width="40%" height={14} />
      </div>
    </div>
  );
}

export function CardSkeleton({ lines = 3 }: { lines?: number }) {
  return (
    <div
      className="card-base"
      style={{ padding: 16, display: "flex", flexDirection: "column", gap: 10 }}
    >
      <Skeleton width="40%" height={14} />
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={`${70 + Math.random() * 30}%`}
          height={12}
        />
      ))}
    </div>
  );
}
