import { type ChangeEvent, type DragEvent, useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import clsx from "clsx";
import { ACCEPTED_FILE_EXTENSIONS } from "@/types/upload";

interface DropzoneProps {
  onFilesSelected: (files: File[]) => void;
}

export function Dropzone({ onFilesSelected }: DropzoneProps) {
  const [isDragActive, setIsDragActive] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setIsDragActive(false);
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) onFilesSelected(files);
  }

  function handleInputChange(e: ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length > 0) onFilesSelected(files);
    e.target.value = ""; // allow re-selecting the same file
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragActive(true);
      }}
      onDragLeave={() => setIsDragActive(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") inputRef.current?.click();
      }}
      className={clsx(
        "flex flex-col items-center justify-center gap-3 rounded-card border-2 border-dashed p-10 text-center cursor-pointer transition-colors",
        isDragActive
          ? "border-signal-400 bg-signal-500/5"
          : "border-surface-700 hover:border-surface-600 bg-surface-900"
      )}
    >
      <UploadCloud className={clsx("h-8 w-8", isDragActive ? "text-signal-400" : "text-surface-400")} />
      <div>
        <p className="text-sm font-medium text-surface-100">
          Drag and drop files here, or click to browse
        </p>
        <p className="text-xs text-surface-400 mt-1">
          Supports CSV, XLSX, PDF, DOCX, PNG, JPG
        </p>
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED_FILE_EXTENSIONS.join(",")}
        onChange={handleInputChange}
        className="hidden"
      />
    </div>
  );
}
