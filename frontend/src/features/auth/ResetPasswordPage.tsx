import { type FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { Boxes } from "lucide-react";
import { authApi } from "@/api/auth";
import { getApiErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const token = searchParams.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await authApi.confirmPasswordReset(token, newPassword);
      navigate("/login");
    } catch (err) {
      setError(getApiErrorMessage(err, "This reset link is invalid or expired."));
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
          <h1 className="text-lg font-semibold text-surface-100 mb-1">Set a new password</h1>
          <p className="text-sm text-surface-400 mb-6">
            Choose a new password for your account.
          </p>

          {!token ? (
            <p className="field-error">
              This link is missing a reset token. Please request a new one.
            </p>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <Input
                label="New password"
                type="password"
                autoComplete="new-password"
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              {error && <p className="field-error">{error}</p>}
              <Button type="submit" isLoading={isLoading}>
                Reset password
              </Button>
            </form>
          )}
        </Card>

        <p className="text-center text-sm text-surface-400 mt-6">
          <Link to="/login" className="text-signal-400 hover:text-signal-300 font-medium">
            Back to log in
          </Link>
        </p>
      </div>
    </div>
  );
}
