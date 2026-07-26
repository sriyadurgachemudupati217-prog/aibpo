import { useEffect } from "react";
import { Dropzone } from "@/components/upload/Dropzone";
import { UploadList } from "@/components/upload/UploadList";
import { Card } from "@/components/ui/Card";
import { useUploadStore } from "@/store/uploadStore";

const STATUS_POLL_INTERVAL_MS = 3000;

export default function UploadCenterPage() {
  const { uploads, pendingUploads, listError, fetchUploads, uploadFiles, removeUpload, refreshStatuses } =
    useUploadStore();

  useEffect(() => {
    fetchUploads();
  }, [fetchUploads]);

  // Auto-refresh: while any upload is still pending/processing, poll its
  // status so the badge flips to Done/Failed without a manual reload.
  useEffect(() => {
    const hasInFlight = uploads.some((u) => u.status === "pending" || u.status === "processing");
    if (!hasInFlight) return;

    const interval = setInterval(refreshStatuses, STATUS_POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [uploads, refreshStatuses]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-surface-100">Upload Center</h1>
        <p className="text-sm text-surface-400 mt-1">
          Upload task history, tickets, sales data, meeting transcripts, and more for analysis.
        </p>
      </div>

      <Dropzone onFilesSelected={uploadFiles} />

      <Card>
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-sm font-semibold text-surface-100">Files</h2>
          {listError && <p className="text-xs text-danger">{listError}</p>}
        </div>
        <UploadList uploads={uploads} pendingUploads={pendingUploads} onDelete={removeUpload} />
      </Card>
    </div>
  );
}
