import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";

import { AuthShell } from "@/pages/LoginPage";
import { apiErrorMessage } from "@/lib/api";
import { forgotPassword, resetPassword } from "@/services/auth";

export function ForgotPasswordPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<"request" | "reset">("request");
  const [email, setEmail] = useState("");
  const [token, setToken] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleRequest(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await forgotPassword(email);
      toast.success(res.message);
      // In development the backend returns the reset token so the flow is
      // testable without an email provider.
      if (res.reset_token) {
        setToken(res.reset_token);
        toast("Dev mode: reset token pre-filled", { icon: "🔑" });
      }
      setStep("reset");
    } catch (err) {
      toast.error(apiErrorMessage(err, "Could not start reset"));
    } finally {
      setLoading(false);
    }
  }

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    if (newPassword.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    try {
      await resetPassword(token, newPassword);
      toast.success("Password updated. Please sign in.");
      navigate("/login");
    } catch (err) {
      toast.error(apiErrorMessage(err, "Could not reset password"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell>
      <motion.div
        className="card w-full max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-2xl font-bold">Reset password</h2>
        <p className="mt-1 text-sm text-slate-500">
          {step === "request"
            ? "Enter your email to receive a reset token"
            : "Enter the reset token and your new password"}
        </p>

        {step === "request" ? (
          <form onSubmit={handleRequest} className="mt-6 space-y-4">
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                className="input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading && <Loader2 className="animate-spin" size={16} />}
              Send reset token
            </button>
          </form>
        ) : (
          <form onSubmit={handleReset} className="mt-6 space-y-4">
            <div>
              <label className="label">Reset token</label>
              <textarea
                className="input min-h-[80px] break-all font-mono text-xs"
                value={token}
                onChange={(e) => setToken(e.target.value)}
                required
              />
            </div>
            <div>
              <label className="label">New password</label>
              <input
                type="password"
                className="input"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
                autoComplete="new-password"
              />
            </div>
            <button type="submit" className="btn-primary w-full" disabled={loading}>
              {loading && <Loader2 className="animate-spin" size={16} />}
              Update password
            </button>
          </form>
        )}

        <p className="mt-4 text-center text-sm text-slate-500">
          Remembered it?{" "}
          <Link to="/login" className="font-semibold text-brand-600">
            Back to sign in
          </Link>
        </p>
      </motion.div>
    </AuthShell>
  );
}
