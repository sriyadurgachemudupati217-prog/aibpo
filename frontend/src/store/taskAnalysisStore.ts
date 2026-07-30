import { create } from "zustand";
import { tasksApi } from "@/api/tasks";
import type {
  DelayPrediction,
  DepartmentBottleneck,
  RedistributionRecommendation,
  RepetitiveTaskGroup,
  WorkloadAnalysis,
} from "@/types/task";

interface TaskAnalysisState {
  workload: WorkloadAnalysis | null;
  bottlenecks: DepartmentBottleneck[];
  repetitiveWork: RepetitiveTaskGroup[];
  redistribution: RedistributionRecommendation[];
  delayPredictions: DelayPrediction[];
  isLoading: boolean;
  error: string | null;
  fetchAll: () => Promise<void>;
}

function getErrorMessage(err: unknown): string {
  if (err instanceof Error) return err.message;
  return "Could not load task analysis.";
}

export const useTaskAnalysisStore = create<TaskAnalysisState>((set) => ({
  workload: null,
  bottlenecks: [],
  repetitiveWork: [],
  redistribution: [],
  delayPredictions: [],
  isLoading: false,
  error: null,

  fetchAll: async () => {
    set({ isLoading: true, error: null });
    try {
      const [workload, bottlenecks, repetitiveWork, redistribution, delayPredictions] = await Promise.all([
        tasksApi.workloadAnalysis(),
        tasksApi.bottlenecks(),
        tasksApi.repetitiveWork(),
        tasksApi.redistribution(),
        tasksApi.delayPredictions(),
      ]);
      set({
        workload,
        bottlenecks,
        repetitiveWork,
        redistribution,
        delayPredictions,
        isLoading: false,
      });
    } catch (err) {
      set({ error: getErrorMessage(err), isLoading: false });
    }
  },
}));
