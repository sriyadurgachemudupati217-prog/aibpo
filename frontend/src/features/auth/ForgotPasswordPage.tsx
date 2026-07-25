import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";
import { Boxes } from "lucide-react";
import { authApi } from "@/api/auth";
import { getApiErrorMessage } from "@/api/client";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      await authApi.requestPasswordReset(email);
      setSubmitted(true);
    } catch (err) {
      setError(getApiErrorMessage(err));
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
          {submitted ? (
            <>
              <h1 className="text-lg font-semibold text-surface-100 mb-1">Check your email</h1>
              <p className="text-sm text-surface-400">
                If an account exists for <span className="text-surface-200">{email}</span>, we&apos;ve
                sent a link to reset your password.
              </p>
            </>
          ) : (
            <>
              <h1 className="text-lg font-semibold text-surface-100 mb-1">Reset your password</h1>
              <p className="text-sm text-surface-400 mb-6">
                Enter your email and we&apos;ll send you a reset link.
              </p>
              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  label="Work email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                {error && <p className="field-error">{error}</p>}
                <Button type="submit" isLoading={isLoading}>
                  Send reset link
                </Button>
              </form>
            </>
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
