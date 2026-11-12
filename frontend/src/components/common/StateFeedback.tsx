import React from "react";
import { AlertCircle, CheckCircle2, Info, RefreshCw, Inbox } from "lucide-react";

export const CardSkeleton: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className = "",
}) => (
  <div className={`rm-card p-5 animate-pulse ${className}`} aria-busy="true">
    <div className="h-4 w-1/3 rounded bg-mint mb-4" />
    <div className="space-y-2.5">
      {Array.from({ length: lines }).map((_, idx) => (
        <div
          key={idx}
          className={`h-3 rounded bg-mint/80 ${idx === lines - 1 ? "w-2/3" : "w-full"}`}
        />
      ))}
    </div>
  </div>
);

export const EmptyState: React.FC<{
  title: string;
  description: string;
  action?: React.ReactNode;
}> = ({ title, description, action }) => (
  <div className="rm-card p-8 text-center flex flex-col items-center justify-center gap-3">
    <div className="h-12 w-12 rounded-2xl bg-mint flex items-center justify-center text-forest">
      <Inbox className="h-6 w-6" />
    </div>
    <h3 className="text-base font-semibold text-ink">{title}</h3>
    <p className="text-sm text-muted max-w-md">{description}</p>
    {action && <div className="mt-2">{action}</div>}
  </div>
);

export const ErrorState: React.FC<{
  message: string;
  onRetry?: () => void;
}> = ({ message, onRetry }) => (
  <div className="rounded-2xl border border-danger/30 bg-danger/5 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
    <div className="flex items-start gap-3">
      <AlertCircle className="h-5 w-5 text-danger shrink-0 mt-0.5" />
      <div>
        <p className="text-sm font-semibold text-ink">Unable to complete request</p>
        <p className="text-xs text-muted mt-0.5">{message}</p>
      </div>
    </div>
    {onRetry && (
      <button onClick={onRetry} className="rm-btn-secondary text-xs px-3 py-2 shrink-0">
        <RefreshCw className="h-3.5 w-3.5" />
        Retry
      </button>
    )}
  </div>
);

export const SuccessBanner: React.FC<{ message: string }> = ({ message }) => (
  <div className="rounded-2xl border border-leaf/30 bg-mint px-4 py-3 flex items-center gap-2.5 text-sm text-deep">
    <CheckCircle2 className="h-4 w-4 text-forest shrink-0" />
    <span>{message}</span>
  </div>
);

export const IntegrationStatusBadge: React.FC<{
  status: "configured" | "not_configured" | "unavailable" | "error" | "ready" | string;
  label?: string;
}> = ({ status, label }) => {
  const isOk = status === "configured" || status === "ready" || status === "ok";
  const isWarn = status === "not_configured" || status === "unavailable";
  const styles = isOk
    ? "bg-mint text-forest border-leaf/30"
    : isWarn
    ? "bg-warning/15 text-[#8A5B00] border-warning/40"
    : "bg-danger/10 text-danger border-danger/30";

  const text =
    label ||
    (isOk
      ? "Configured"
      : status === "not_configured"
      ? "Not Configured"
      : status === "unavailable"
      ? "Unavailable"
      : "Error");

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${styles}`}>
      <Info className="h-3 w-3" />
      {text}
    </span>
  );
};
