import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { useState } from "react";
import toast from "react-hot-toast";
import { Link, useNavigate } from "react-router-dom";

import { AuthShell } from "@/pages/LoginPage";
import { useAuth } from "@/context/AuthContext";
import { apiErrorMessage } from "@/lib/api";

export function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    try {
      await register(email, fullName, password);
      toast.success("Account created!");
      navigate("/");
    } catch (err) {
      toast.error(apiErrorMessage(err, "Could not register"));
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
        <h2 className="text-2xl font-bold">Create account</h2>
        <p className="mt-1 text-sm text-slate-500">Start screening candidates today</p>

        <div className="mt-6 space-y-4">
          <div>
            <label className="label">Full name</label>
            <input
              className="input"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>
          <div>
            <label className="label">Email</label>
            <input
              type="email"
              className="input"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
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
              minLength={8}
            />
          </div>
        </div>

        <button type="submit" className="btn-primary mt-6 w-full" disabled={loading}>
          {loading && <Loader2 className="animate-spin" size={16} />}
          Create account
        </button>

        <p className="mt-4 text-center text-sm text-slate-500">
          Already have an account?{" "}
          <Link to="/login" className="font-semibold text-brand-600">
            Sign in
          </Link>
        </p>
      </motion.form>
    </AuthShell>
  );
}
