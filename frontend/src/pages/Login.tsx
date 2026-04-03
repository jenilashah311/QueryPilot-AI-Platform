import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const t = await api<{ access_token: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      localStorage.setItem("token", t.access_token);
      nav("/app");
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Login failed");
    }
  }

  return (
    <div className="layout">
      <h1>Sign in</h1>
      <p style={{ color: "#9fb0c8" }}>Multi-tenant analytics workspace</p>
      <div className="card">
        <form onSubmit={onSubmit}>
          <label>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
          <label style={{ marginTop: "0.75rem" }}>Password</label>
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            required
          />
          {err && <p className="error">{err}</p>}
          <div style={{ marginTop: "1rem" }}>
            <button className="primary" type="submit">
              Continue
            </button>
          </div>
        </form>
      </div>
      <p>
        No account? <Link to="/register">Create workspace</Link>
      </p>
    </div>
  );
}
