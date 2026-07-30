import { FileText, Trash2, AlertCircle } from "lucide-react";
import { StatusBadge } from "@/components/upload/StatusBadge";
import type { PendingUpload } from "@/store/uploadStore";
import { UPLOAD_CATEGORY_LABELS, type Upload } from "@/types/upload";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

interface UploadListProps {
  uploads: Upload[];
  pendingUploads: PendingUpload[];
  onDelete: (id: string) => void;
}

export function UploadList({ uploads, pendingUploads, onDelete }: UploadListProps) {
  if (uploads.length === 0 && pendingUploads.length === 0) {
    return (
      <div className="text-center py-12 text-surface-400 text-sm">
        No files uploaded yet. Drag a file above to get started.
      </div>
    );
  }

  return (
    <div className="divide-y divide-surface-800">
      {pendingUploads.map((p) => (
        <div key={p.tempId} className="flex items-center gap-4 py-3">
          <FileText className="h-5 w-5 text-surface-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-surface-100 truncate">{p.filename}</p>
            {p.error ? (
              <p className="text-xs text-danger flex items-center gap-1 mt-1">
                <AlertCircle className="h-3.5 w-3.5" />
                {p.error}
              </p>
            ) : (
              <div className="h-1.5 bg-surface-800 rounded-full mt-2 overflow-hidden">
                <div
                  className="h-full bg-signal-500 transition-all duration-200"
                  style={{ width: `${p.progress}%` }}
                />
              </div>
            )}
          </div>
          <span className="text-xs text-surface-400 shrink-0">Uploading… {p.progress}%</span>
        </div>
      ))}

      {uploads.map((u) => (
        <div key={u.id} className="flex items-center gap-4 py-3">
          <FileText className="h-5 w-5 text-surface-400 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-surface-100 truncate">{u.original_filename}</p>
            <p className="text-xs text-surface-400 mt-0.5">
              {UPLOAD_CATEGORY_LABELS[u.category]} · {formatBytes(u.file_size_bytes)} · Uploaded{" "}
              {formatDate(u.created_at)}
            </p>
            {u.status === "failed" && u.error_message && (
              <p className="text-xs text-danger flex items-center gap-1 mt-1">
                <AlertCircle className="h-3.5 w-3.5" />
                {u.error_message}
              </p>
            )}
          </div>
          <StatusBadge status={u.status} />
          <button
            onClick={() => onDelete(u.id)}
            className="text-surface-400 hover:text-danger transition-colors shrink-0"
            aria-label={`Delete ${u.original_filename}`}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}
