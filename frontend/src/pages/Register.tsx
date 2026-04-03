import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api";

export default function Register() {
  const nav = useNavigate();
  const [workspaceName, setWorkspaceName] = useState("Demo Co");
  const [email, setEmail] = useState("you@example.com");
  const [password, setPassword] = useState("password123");
  const [err, setErr] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const t = await api<{ access_token: string }>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ workspace_name: workspaceName, email, password }),
      });
      localStorage.setItem("token", t.access_token);
      nav("/app");
    } catch (ex) {
      setErr(ex instanceof Error ? ex.message : "Registration failed");
    }
  }

  return (
    <div className="layout">
      <h1>Create workspace</h1>
      <p style={{ color: "#9fb0c8" }}>Schema-per-tenant isolation on PostgreSQL</p>
      <div className="card">
        <form onSubmit={onSubmit}>
          <label>Workspace name</label>
          <input value={workspaceName} onChange={(e) => setWorkspaceName(e.target.value)} required />
          <label style={{ marginTop: "0.75rem" }}>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
          <label style={{ marginTop: "0.75rem" }}>Password (min 8)</label>
          <input
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            minLength={8}
            required
          />
          {err && <p className="error">{err}</p>}
          <div style={{ marginTop: "1rem" }}>
            <button className="primary" type="submit">
              Register
            </button>
          </div>
        </form>
      </div>
      <p>
        Already have an account? <Link to="/login">Sign in</Link>
      </p>
    </div>
  );
}
