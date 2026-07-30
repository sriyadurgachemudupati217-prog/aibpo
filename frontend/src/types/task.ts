export type TaskStatus = "not_started" | "in_progress" | "completed" | "blocked";

export interface Task {
  id: string;
  upload_id: string | null;
  employee_id: string | null;
  task_name: string;
  department: string | null;
  status: TaskStatus;
  assigned_at: string | null;
  due_at: string | null;
  completed_at: string | null;
  estimated_hours: number | null;
  actual_hours: number | null;
  delay_probability: number | null;
}

export type WorkloadFlag = "overloaded" | "underloaded" | "balanced";

export interface EmployeeWorkload {
  employee_id: string;
  display_name: string;
  department: string | null;
  task_count: number;
  total_estimated_hours: number;
  total_actual_hours: number;
  workload_index: number;
  flag: WorkloadFlag;
}

export interface WorkloadAnalysis {
  employees: EmployeeWorkload[];
  department_mean_hours: Record<string, number>;
}

export interface DepartmentBottleneck {
  department: string;
  task_count: number;
  overdue_count: number;
  blocked_count: number;
  avg_hours_overage: number;
  bottleneck_score: number;
  is_bottleneck: boolean;
}

export interface RepetitiveTaskGroup {
  employee_id: string;
  display_name: string;
  task_name: string;
  occurrence_count: number;
  total_hours: number;
  automation_candidate: boolean;
}

export interface RedistributionRecommendation {
  task_id: string;
  task_name: string;
  estimated_hours: number | null;
  from_employee_id: string;
  from_employee_name: string;
  to_employee_id: string;
  to_employee_name: string;
  reason: string;
}

export interface DelayPrediction {
  task_id: string;
  task_name: string;
  employee_id: string | null;
  department: string | null;
  due_at: string | null;
  probability: number;
  method: "xgboost" | "empirical" | "heuristic";
}
