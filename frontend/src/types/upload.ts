export type FileType = "csv" | "xlsx" | "pdf" | "docx" | "png" | "jpg";
export type UploadStatus = "pending" | "processing" | "done" | "failed";
export type UploadCategory =
  | "task_history"
  | "tickets"
  | "sales"
  | "meetings"
  | "attendance"
  | "projects"
  | "other";

export const UPLOAD_CATEGORY_LABELS: Record<UploadCategory, string> = {
  task_history: "Task history",
  tickets: "Support tickets",
  sales: "Sales history",
  meetings: "Meeting transcripts",
  attendance: "Attendance",
  projects: "Project timelines",
  other: "Other",
};

export interface Upload {
  id: string;
  company_id: string;
  uploaded_by: string;
  original_filename: string;
  file_type: FileType;
  category: UploadCategory;
  status: UploadStatus;
  file_size_bytes: number;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface UploadStatusRead {
  id: string;
  status: UploadStatus;
  error_message: string | null;
  updated_at: string;
}

export const ACCEPTED_FILE_EXTENSIONS = [".csv", ".xlsx", ".pdf", ".docx", ".png", ".jpg", ".jpeg"];
