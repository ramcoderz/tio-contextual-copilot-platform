import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";
import { Bot, Mail, Lock, ArrowRight, Loader2, ShieldCheck } from "lucide-react";
import { motion } from "framer-motion";
import { useAppCtx } from "../context/AppContext";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const { setUser } = useAppCtx();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const data = await api("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password })
      });
      localStorage.setItem("token", data.access_token);
      setUser(data.user);
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel auth-card"
      >
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <div style={{ 
            width: '48px', height: '48px', borderRadius: '12px', background: 'var(--accent-glow)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent)',
            margin: '0 auto 16px'
          }}>
            <Bot size={28} />
          </div>
          <h1 style={{ fontSize: '24px', fontWeight: 800 }}>Welcome Back</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '14px', marginTop: '4px' }}>
            Enter your credentials to access TiO.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div className="input-group">
            <label className="input-label">Email Address</label>
            <div className="input-wrapper">
              <Mail size={18} className="input-icon" />
              <input 
                type="email" 
                className="input" 
                placeholder="name@company.com" 
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="input-group">
            <label className="input-label">Password</label>
            <div className="input-wrapper">
              <Lock size={18} className="input-icon" />
              <input 
                type="password" 
                className="input" 
                placeholder="••••••••" 
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
            </div>
          </div>

          {error && (
            <p style={{ color: 'var(--accent-red)', fontSize: '13px', textAlign: 'center' }}>{error}</p>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
            {loading ? <Loader2 size={18} className="animate-spin" /> : "Sign In"}
            {!loading && <ArrowRight size={18} />}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '14px' }}>
          <span style={{ color: 'var(--text-muted)' }}>Don't have an account?</span>{" "}
          <Link to="/signup" className="link-text">Create one</Link>
        </div>

        <div style={{ marginTop: '32px', paddingTop: '24px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', color: 'var(--text-dim)', fontSize: '11px' }}>
          <ShieldCheck size={14} /> Enterprise Grade Security
        </div>
      </motion.div>
    </div>
  );
}
