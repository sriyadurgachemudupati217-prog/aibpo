import { useAuthStore } from "@/store/authStore";
import { Card } from "@/components/ui/Card";

const PLACEHOLDER_KPIS = [
  { label: "Productivity Score", value: "—" },
  { label: "Employee Utilization", value: "—" },
  { label: "Revenue Forecast", value: "—" },
  { label: "Delay Probability", value: "—" },
];

export default function DashboardHome() {
  const user = useAuthStore((s) => s.user);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-surface-100">
          Welcome{user ? `, ${user.full_name.split(" ")[0]}` : ""}
        </h1>
        <p className="text-sm text-surface-400 mt-1">
          Here&apos;s your workspace overview. Upload data to populate these insights.
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {PLACEHOLDER_KPIS.map((kpi) => (
          <Card key={kpi.label}>
            <p className="kpi-label">{kpi.label}</p>
            <p className="kpi-value mt-2">{kpi.value}</p>
          </Card>
        ))}
      </div>

      <Card>
        <p className="text-sm text-surface-400">
          Task, ticket, sales, and meeting analysis modules will appear here once their
          upload pipelines are built in the next phases.
        </p>
      </Card>
    </div>
  );
}
