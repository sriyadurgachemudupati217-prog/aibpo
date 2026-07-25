import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Boxes } from "lucide-react";
import { authApi } from "@/api/auth";
import { getApiErrorMessage } from "@/api/client";
import { useAuthStore } from "@/store/authStore";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

const PASSWORD_HINT = "At least 8 characters, with an uppercase letter, a lowercase letter, and a digit.";

export default function SignupPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);

  const [companyName, setCompanyName] = useState("");
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const tokens = await authApi.register({
        company_name: companyName,
        full_name: fullName,
        email,
        password,
      });
      setTokens(tokens);
      navigate("/dashboard");
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not create your workspace."));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-950 px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-2 justify-center mb-8">
          <Boxes className="h-6 w-6 text-signal-400" />
          <span className="font-semibold text-surface-100 tracking-tight">AI Process Optimizer</span>
        </div>

        <Card>
          <h1 className="text-lg font-semibold text-surface-100 mb-1">Create your workspace</h1>
          <p className="text-sm text-surface-400 mb-6">You&apos;ll be the admin for your company.</p>

          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Company name"
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
            />
            <Input
              label="Your full name"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
            <Input
              label="Work email"
              type="email"
              autoComplete="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            <div>
              <Input
                label="Password"
                type="password"
                autoComplete="new-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
              <p className="text-xs text-surface-400 mt-1.5">{PASSWORD_HINT}</p>
            </div>

            {error && <p className="field-error">{error}</p>}

            <Button type="submit" isLoading={isLoading}>
              Create workspace
            </Button>
          </form>
        </Card>

        <p className="text-center text-sm text-surface-400 mt-6">
          Already have a workspace?{" "}
          <Link to="/login" className="text-signal-400 hover:text-signal-300 font-medium">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}
