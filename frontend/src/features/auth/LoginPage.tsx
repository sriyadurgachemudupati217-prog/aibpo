import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Boxes } from "lucide-react";
import { authApi } from "@/api/auth";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const tokens = await authApi.login({ email, password });
      setTokens(tokens);
      navigate("/dashboard");
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not log in. Check your credentials."));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950 px-4">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <Boxes className="h-6 w-6 text-signal-400" />
          <span className="font-semibold text-surface-100 tracking-tight">AI Process Optimizer</span>
        </div>

        <Card>
          <h1 className="text-lg font-semibold text-surface-100 mb-1">Welcome back</h1>
          <p className="text-sm text-surface-400 mb-6">Log in to your workspace.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Work email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />

            {error && <p className="field-error">{error}</p>}

            <div className="flex justify-end -mt-2">
              <Link to="/forgot-password" className="text-xs text-signal-400 hover:text-signal-300">
                Forgot password?
              </Link>
            </div>

            <Button type="submit" isLoading={isLoading}>
              Log in
            </Button>
          </form>
        </Card>

        <p className="text-center text-sm text-surface-400 mt-6">
          Don&apos;t have a workspace yet?{" "}
          <Link to="/signup" className="text-signal-400 hover:text-signal-300 font-medium">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
