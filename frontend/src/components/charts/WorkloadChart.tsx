import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { EmployeeWorkload } from "@/types/task";

const FLAG_COLORS: Record<EmployeeWorkload["flag"], string> = {
  overloaded: "#F4657A", // danger
  underloaded: "#5EA1F2", // data-sky
  balanced: "#2DD4BF", // data-teal
};

interface WorkloadChartProps {
  employees: EmployeeWorkload[];
}

export function WorkloadChart({ employees }: WorkloadChartProps) {
  const data = employees.map((e) => ({
    name: e.display_name,
    hours: e.total_estimated_hours,
    flag: e.flag,
  }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2A3141" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: "#7B869C", fontSize: 12 }} axisLine={{ stroke: "#2A3141" }} />
        <YAxis tick={{ fill: "#7B869C", fontSize: 12 }} axisLine={{ stroke: "#2A3141" }} />
        <Tooltip
          contentStyle={{
            background: "#11151D",
            border: "1px solid #1D2330",
            borderRadius: 8,
            fontSize: 12,
          }}
          labelStyle={{ color: "#E7EAF0" }}
        />
        <Bar dataKey="hours" radius={[4, 4, 0, 0]}>
          {data.map((entry, i) => (
            <Cell key={i} fill={FLAG_COLORS[entry.flag]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
