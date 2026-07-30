import { apiClient } from "@/api/client";
import type {
  DelayPrediction,
  DepartmentBottleneck,
  RedistributionRecommendation,
  RepetitiveTaskGroup,
  Task,
  WorkloadAnalysis,
} from "@/types/task";

export const tasksApi = {
  list: () => apiClient.get<Task[]>("/tasks").then((r) => r.data),

  workloadAnalysis: () => apiClient.get<WorkloadAnalysis>("/tasks/analysis").then((r) => r.data),

  bottlenecks: () => apiClient.get<DepartmentBottleneck[]>("/tasks/bottlenecks").then((r) => r.data),

  repetitiveWork: () => apiClient.get<RepetitiveTaskGroup[]>("/tasks/repetitive").then((r) => r.data),

  redistribution: () =>
    apiClient.get<RedistributionRecommendation[]>("/tasks/redistribution").then((r) => r.data),

  delayPredictions: () => apiClient.get<DelayPrediction[]>("/tasks/delay-predictions").then((r) => r.data),
};
