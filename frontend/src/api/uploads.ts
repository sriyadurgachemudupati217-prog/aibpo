import { apiClient } from "@/api/client";
import type { Upload, UploadCategory, UploadStatusRead } from "@/types/upload";

export const uploadsApi = {
  create: (file: File, category: UploadCategory, onUploadProgress?: (percent: number) => void) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("category", category);
    return apiClient
      .post<Upload>("/uploads", formData, {
        headers: { "Content-Type": "multipart/form-data" },
        onUploadProgress: (event) => {
          if (onUploadProgress && event.total) {
            onUploadProgress(Math.round((event.loaded / event.total) * 100));
          }
        },
      })
      .then((r) => r.data);
  },

  list: () => apiClient.get<Upload[]>("/uploads").then((r) => r.data),

  get: (id: string) => apiClient.get<Upload>(`/uploads/${id}`).then((r) => r.data),

  getStatus: (id: string) =>
    apiClient.get<UploadStatusRead>(`/uploads/${id}/status`).then((r) => r.data),

  remove: (id: string) => apiClient.delete(`/uploads/${id}`).then((r) => r.data),
};
