import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import clsx from "clsx";
import type { UploadStatus } from "@/types/upload";

const STATUS_CONFIG: Record<
  UploadStatus,
  { label: string; className: string; icon: typeof Clock }
> = {
  pending: { label: "Pending", className: "text-surface-400 bg-surface-800", icon: Clock },
  processing: {
    label: "Processing",
    className: "text-data-sky bg-data-sky/10",
    icon: Loader2,
  },
  done: { label: "Done", className: "text-success bg-success/10", icon: CheckCircle2 },
  failed: { label: "Failed", className: "text-danger bg-danger/10", icon: XCircle },
};

export function StatusBadge({ status }: { status: UploadStatus }) {
  const config = STATUS_CONFIG[status];
  const Icon = config.icon;

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium",
        config.className
      )}
    >
      <Icon className={clsx("h-3.5 w-3.5", status === "processing" && "animate-spin")} />
      {config.label}
    </span>
  );
}
