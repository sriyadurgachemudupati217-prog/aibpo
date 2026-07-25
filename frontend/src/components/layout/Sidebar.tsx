import { NavLink } from "react-router-dom";
import {
  Boxes,
  LayoutDashboard,
  ListChecks,
  LifeBuoy,
  TrendingUp,
  Users,
  FileText,
  Settings,
  X,
} from "lucide-react";
import clsx from "clsx";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/dashboard/tasks", label: "Tasks", icon: ListChecks },
  { to: "/dashboard/support", label: "Support", icon: LifeBuoy },
  { to: "/dashboard/sales", label: "Sales", icon: TrendingUp },
  { to: "/dashboard/reports", label: "Reports", icon: FileText },
  { to: "/dashboard/team", label: "Team", icon: Users },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-40 w-64 bg-surface-900 border-r border-surface-800 flex flex-col",
          "transition-transform duration-200 lg:translate-x-0 lg:static lg:z-auto",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-surface-800">
          <div className="flex items-center gap-2">
            <Boxes className="h-5 w-5 text-signal-400" />
            <span className="font-semibold text-surface-100 text-sm tracking-tight">
              AI Process Optimizer
            </span>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden text-surface-400 hover:text-surface-100"
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                clsx(
                  "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-signal-500/15 text-signal-400"
                    : "text-surface-400 hover:text-surface-100 hover:bg-surface-800"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="p-3 border-t border-surface-800">
          <NavLink
            to="/dashboard/settings"
            className={({ isActive }) =>
              clsx(
                "flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium transition-colors",
                isActive
                  ? "bg-signal-500/15 text-signal-400"
                  : "text-surface-400 hover:text-surface-100 hover:bg-surface-800"
              )
            }
          >
            <Settings className="h-4 w-4" />
            Settings
          </NavLink>
        </div>
      </aside>
    </>
  );
}
