import { useEffect } from "react";
import { AlertTriangle, ArrowRightLeft, Repeat, TrendingDown } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { WorkloadChart } from "@/components/charts/WorkloadChart";
import { useTaskAnalysisStore } from "@/store/taskAnalysisStore";

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export default function TaskAnalysisPage() {
  const { workload, bottlenecks, repetitiveWork, redistribution, delayPredictions, isLoading, error, fetchAll } =
    useTaskAnalysisStore();

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  const overloadedCount = workload?.employees.filter((e) => e.flag === "overloaded").length ?? 0;
  const bottleneckCount = bottlenecks.filter((b) => b.is_bottleneck).length;
  const highRiskCount = delayPredictions.filter((p) => p.probability >= 0.6).length;
  const automationCandidates = repetitiveWork.filter((r) => r.automation_candidate).length;

  if (error) {
    return (
      <Card>
        <p className="text-sm text-danger">{error}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-surface-100">Task Analysis</h1>
        <p className="text-sm text-surface-400 mt-1">
          Workload, bottlenecks, repetitive work, and delay risk from your uploaded task history.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <p className="kpi-label">Overloaded Employees</p>
          <p className="kpi-value mt-2">{isLoading ? "—" : overloadedCount}</p>
        </Card>
        <Card>
          <p className="kpi-label">Bottleneck Departments</p>
          <p className="kpi-value mt-2">{isLoading ? "—" : bottleneckCount}</p>
        </Card>
        <Card>
          <p className="kpi-label">High Delay-Risk Tasks</p>
          <p className="kpi-value mt-2">{isLoading ? "—" : highRiskCount}</p>
        </Card>
        <Card>
          <p className="kpi-label">Automation Candidates</p>
          <p className="kpi-value mt-2">{isLoading ? "—" : automationCandidates}</p>
        </Card>
      </div>

      <Card>
        <h2 className="text-sm font-semibold text-surface-100 mb-4">Workload by Employee</h2>
        {workload && workload.employees.length > 0 ? (
          <WorkloadChart employees={workload.employees} />
        ) : (
          <p className="text-sm text-surface-400 py-8 text-center">
            No task data yet — upload a task-history file to see workload distribution.
          </p>
        )}
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <div className="flex items-center gap-2 mb-4">
            <AlertTriangle className="h-4 w-4 text-signal-400" />
            <h2 className="text-sm font-semibold text-surface-100">Department Bottlenecks</h2>
          </div>
          {bottlenecks.length === 0 ? (
            <p className="text-sm text-surface-400">No department data yet.</p>
          ) : (
            <div className="space-y-2">
              {bottlenecks.map((b) => (
                <div
                  key={b.department}
                  className="flex items-center justify-between py-2 border-b border-surface-800 last:border-0"
                >
                  <div>
                    <p className="text-sm text-surface-100">{b.department}</p>
                    <p className="text-xs text-surface-400">
                      {b.overdue_count} overdue · {b.blocked_count} blocked · {b.task_count} tasks
                    </p>
                  </div>
                  {b.is_bottleneck && (
                    <span className="text-xs font-medium text-danger bg-danger/10 px-2 py-1 rounded-full">
                      Bottleneck
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <div className="flex items-center gap-2 mb-4">
            <Repeat className="h-4 w-4 text-signal-400" />
            <h2 className="text-sm font-semibold text-surface-100">Repetitive Work</h2>
          </div>
          {repetitiveWork.length === 0 ? (
            <p className="text-sm text-surface-400">No repeated tasks detected yet.</p>
          ) : (
            <div className="space-y-2">
              {repetitiveWork.slice(0, 8).map((r, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between py-2 border-b border-surface-800 last:border-0"
                >
                  <div>
                    <p className="text-sm text-surface-100">{r.task_name}</p>
                    <p className="text-xs text-surface-400">
                      {r.display_name} · {r.occurrence_count}× · {r.total_hours}h
                    </p>
                  </div>
                  {r.automation_candidate && (
                    <span className="text-xs font-medium text-signal-400 bg-signal-500/10 px-2 py-1 rounded-full">
                      Automate
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>

      <Card>
        <div className="flex items-center gap-2 mb-4">
          <ArrowRightLeft className="h-4 w-4 text-signal-400" />
          <h2 className="text-sm font-semibold text-surface-100">Redistribution Recommendations</h2>
        </div>
        {redistribution.length === 0 ? (
          <p className="text-sm text-surface-400">
            No redistribution needed right now — workload looks balanced.
          </p>
        ) : (
          <div className="divide-y divide-surface-800">
            {redistribution.map((r) => (
              <div key={r.task_id} className="py-3">
                <p className="text-sm text-surface-100">
                  Move <span className="font-medium">{r.task_name}</span> from{" "}
                  <span className="font-medium">{r.from_employee_name}</span> to{" "}
                  <span className="font-medium">{r.to_employee_name}</span>
                </p>
                <p className="text-xs text-surface-400 mt-1">{r.reason}</p>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <div className="flex items-center gap-2 mb-4">
          <TrendingDown className="h-4 w-4 text-signal-400" />
          <h2 className="text-sm font-semibold text-surface-100">Delay Risk</h2>
        </div>
        {delayPredictions.length === 0 ? (
          <p className="text-sm text-surface-400">No open tasks with due dates to score yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-surface-400 uppercase tracking-wide">
                <th className="pb-2 font-medium">Task</th>
                <th className="pb-2 font-medium">Department</th>
                <th className="pb-2 font-medium">Due</th>
                <th className="pb-2 font-medium text-right">Delay risk</th>
              </tr>
            </thead>
            <tbody>
              {delayPredictions.slice(0, 10).map((p) => (
                <tr key={p.task_id} className="border-t border-surface-800">
                  <td className="py-2 text-surface-100">{p.task_name}</td>
                  <td className="py-2 text-surface-400">{p.department ?? "—"}</td>
                  <td className="py-2 text-surface-400">
                    {p.due_at ? new Date(p.due_at).toLocaleDateString() : "—"}
                  </td>
                  <td className="py-2 text-right">
                    <span
                      className={
                        p.probability >= 0.6
                          ? "text-danger font-medium"
                          : p.probability >= 0.3
                            ? "text-warning font-medium"
                            : "text-success font-medium"
                      }
                    >
                      {formatPercent(p.probability)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
