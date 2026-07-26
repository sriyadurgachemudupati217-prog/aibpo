import { create } from "zustand";
import { uploadsApi } from "@/api/uploads";
import type { Upload } from "@/types/upload";

export interface PendingUpload {
  tempId: string;
  filename: string;
  progress: number;
  error: string | null;
}

interface UploadState {
  uploads: Upload[];
  pendingUploads: PendingUpload[];
  isLoading: boolean;
  listError: string | null;

  fetchUploads: () => Promise<void>;
  uploadFiles: (files: File[]) => Promise<void>;
  removeUpload: (id: string) => Promise<void>;
  refreshStatuses: () => Promise<void>;
}

function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "Upload failed.";
}

export const useUploadStore = create<UploadState>((set, get) => ({
  uploads: [],
  pendingUploads: [],
  isLoading: false,
  listError: null,

  fetchUploads: async () => {
    set({ isLoading: true, listError: null });
    try {
      const uploads = await uploadsApi.list();
      set({ uploads, isLoading: false });
    } catch (err) {
      set({ listError: getErrorMessage(err), isLoading: false });
    }
  },

  uploadFiles: async (files: File[]) => {
    const newPending: PendingUpload[] = files.map((file, i) => ({
      tempId: `${Date.now()}-${i}-${file.name}`,
      filename: file.name,
      progress: 0,
      error: null,
    }));
    set((state) => ({ pendingUploads: [...state.pendingUploads, ...newPending] }));

    await Promise.all(
      files.map(async (file, i) => {
        const tempId = newPending[i].tempId;
        try {
          const uploaded = await uploadsApi.create(file, (percent) => {
            set((state) => ({
              pendingUploads: state.pendingUploads.map((p) =>
                p.tempId === tempId ? { ...p, progress: percent } : p
              ),
            }));
          });
          set((state) => ({
            uploads: [uploaded, ...state.uploads],
            pendingUploads: state.pendingUploads.filter((p) => p.tempId !== tempId),
          }));
        } catch (err) {
          set((state) => ({
            pendingUploads: state.pendingUploads.map((p) =>
              p.tempId === tempId ? { ...p, error: getErrorMessage(err) } : p
            ),
          }));
        }
      })
    );
  },

  removeUpload: async (id: string) => {
    const previous = get().uploads;
    set({ uploads: previous.filter((u) => u.id !== id) }); // optimistic
    try {
      await uploadsApi.remove(id);
    } catch (err) {
      set({ uploads: previous, listError: getErrorMessage(err) }); // revert on failure
    }
  },

  refreshStatuses: async () => {
    const inFlight = get().uploads.filter(
      (u) => u.status === "pending" || u.status === "processing"
    );
    if (inFlight.length === 0) return;

    const results = await Promise.allSettled(
      inFlight.map((u) => uploadsApi.getStatus(u.id))
    );

    set((state) => {
      const byId = new Map(
        results
          .map((r, i) => (r.status === "fulfilled" ? ([inFlight[i].id, r.value] as const) : null))
          .filter((entry): entry is readonly [string, Awaited<ReturnType<typeof uploadsApi.getStatus>>] => entry !== null)
      );
      return {
        uploads: state.uploads.map((u) => {
          const fresh = byId.get(u.id);
          return fresh ? { ...u, status: fresh.status, error_message: fresh.error_message } : u;
        }),
      };
    });
  },
}));
