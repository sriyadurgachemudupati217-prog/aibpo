import { useEffect, useState } from "react";
import { Dropzone } from "@/components/upload/Dropzone";
import { UploadList } from "@/components/upload/UploadList";
import { Card } from "@/components/ui/Card";
import { useUploadStore } from "@/store/uploadStore";
import { UPLOAD_CATEGORY_LABELS, type UploadCategory } from "@/types/upload";

const STATUS_POLL_INTERVAL_MS = 3000;

export default function UploadCenterPage() {
  const { uploads, pendingUploads, listError, fetchUploads, uploadFiles, removeUpload, refreshStatuses } =
    useUploadStore();
  const [category, setCategory] = useState<UploadCategory>("task_history");

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

      <Card>
        <label htmlFor="upload-category" className="block text-sm font-medium text-surface-200 mb-1.5">
          What kind of data is this?
        </label>
        <select
          id="upload-category"
          value={category}
          onChange={(e) => setCategory(e.target.value as UploadCategory)}
          className="input-field mb-4 sm:max-w-xs"
        >
          {Object.entries(UPLOAD_CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <p className="text-xs text-surface-400 mb-4 -mt-2">
          "Task history" files are automatically parsed into the Task Analysis dashboard.
        </p>
        <Dropzone onFilesSelected={(files) => uploadFiles(files, category)} />
      </Card>

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
