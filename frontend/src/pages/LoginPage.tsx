import { motion } from "framer-motion";
import { Loader2, Sparkles } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/context/AuthContext";
import { apiErrorMessage } from "@/lib/api";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      navigate("/");
    } catch (err) {
      toast.error(apiErrorMessage(err, "Invalid credentials"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <AuthShell>
      <motion.form
        onSubmit={handleSubmit}
        className="card w-full max-w-md"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <h2 className="text-2xl font-bold">Sign in</h2>
        <p className="mt-1 text-sm text-slate-500">Access your recruiter dashboard</p>

        <div className="mt-6 space-y-4">
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
          <div>
            <label className="label">Password</label>
            <input
              type="password"
              className="input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </div>
        </div>

        <button type="submit" className="btn-primary mt-6 w-full" disabled={loading}>
          {loading && <Loader2 className="animate-spin" size={16} />}
          Sign in
        </button>

        <p className="mt-3 text-center text-sm">
          <Link to="/forgot-password" className="font-medium text-slate-500 hover:text-brand-600">
            Forgot password?
          </Link>
        </p>

        <p className="mt-2 text-center text-sm text-slate-500">
          No account?{" "}
          <Link to="/register" className="font-semibold text-brand-600">
            Create one
          </Link>
        </p>
      </motion.form>
    </AuthShell>
  );
}

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen">
      <div className="hidden flex-1 flex-col justify-between bg-gradient-to-br from-brand-600 to-brand-800 p-12 text-white lg:flex">
        <div className="flex items-center gap-2 text-xl font-bold">
          <Sparkles /> ScreenAI
        </div>
        <div>
          <h1 className="text-4xl font-bold leading-tight">
            Rank hundreds of resumes in seconds.
          </h1>
          <p className="mt-4 max-w-md text-brand-100">
            AI-powered semantic matching, skill gap analysis, and recruiter-grade
            candidate rankings. Spend time on people, not paperwork.
          </p>
          <div className="mt-8 grid grid-cols-3 gap-4">
            {[
              ["10k+", "Resumes/job"],
              ["<2s", "Semantic search"],
              ["5", "Scoring signals"],
            ].map(([v, l]) => (
              <div key={l} className="rounded-xl bg-white/10 p-4">
                <p className="text-2xl font-bold">{v}</p>
                <p className="text-xs text-brand-100">{l}</p>
              </div>
            ))}
          </div>
        </div>
        <p className="text-sm text-brand-200">Production-ready AI screening platform</p>
      </div>
      <div className="flex flex-1 items-center justify-center p-6">{children}</div>
    </div>
  );
}
