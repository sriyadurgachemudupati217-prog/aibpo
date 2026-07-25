import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Menu, ChevronDown, LogOut } from "lucide-react";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

interface NavbarProps {
  onMenuClick: () => void;
}

export function Navbar({ onMenuClick }: NavbarProps) {
  const navigate = useNavigate();
  const { user, refreshToken, clear } = useAuthStore();
  const [menuOpen, setMenuOpen] = useState(false);

  async function handleLogout() {
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch {
        // Best-effort: clear local session either way.
      }
    }
    clear();
    navigate("/login");
  }

  const initials =
    user?.full_name
      .split(" ")
      .map((part) => part[0])
      .slice(0, 2)
      .join("")
      .toUpperCase() ?? "?";

  return (
    <header className="h-16 flex items-center justify-between px-4 lg:px-6 border-b border-surface-800 bg-surface-950/80 backdrop-blur sticky top-0 z-20">
      <button
        onClick={onMenuClick}
        className="lg:hidden text-surface-300 hover:text-surface-100"
        aria-label="Open sidebar"
      >
        <Menu className="h-5 w-5" />
      </button>

      <div className="hidden lg:block" />

      <div className="relative">
        <button
          onClick={() => setMenuOpen((v) => !v)}
          className="flex items-center gap-2 text-sm text-surface-200 hover:text-surface-100"
        >
          <span className="h-8 w-8 rounded-full bg-signal-500/20 text-signal-400 flex items-center justify-center text-xs font-semibold">
            {initials}
          </span>
          <span className="hidden sm:block font-medium">{user?.full_name ?? "Loading…"}</span>
          <ChevronDown className="h-4 w-4 text-surface-400" />
        </button>

        {menuOpen && (
          <div className="absolute right-0 mt-2 w-48 card p-1 z-30">
            <div className="px-3 py-2 text-xs text-surface-400">
              {user?.role.toUpperCase()} · {user?.email}
            </div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-3 py-2 text-sm text-danger hover:bg-surface-800 rounded-md"
            >
              <LogOut className="h-4 w-4" />
              Log out
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
