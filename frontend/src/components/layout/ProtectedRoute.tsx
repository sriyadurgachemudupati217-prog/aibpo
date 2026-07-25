import { useEffect, useState, type ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { Loader2 } from "lucide-react";
import { authApi } from "@/api/auth";
import { useAuthStore } from "@/store/authStore";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { accessToken, user, setUser, clear } = useAuthStore();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!accessToken) {
      setIsChecking(false);
      return;
    }
    if (user) {
      setIsChecking(false);
      return;
    }
    authApi
      .me()
      .then(setUser)
      .catch(() => clear())
      .finally(() => setIsChecking(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  if (isChecking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-surface-950">
        <Loader2 className="h-6 w-6 text-signal-400 animate-spin" />
      </div>
    );
  }

  if (!accessToken) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
