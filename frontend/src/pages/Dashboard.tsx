import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { formatAxisNumber } from "../chartUtils";
import { ChartRenderer } from "../ChartRenderer";

type Me = {
  email: string;
  role: string;
  workspace: { name: string; plan: string } | null;
};

type QueryOut = {
  sql: string;
  rows: Record<string, string | number>[];
  insight: string;
  columns: string[];
  chart_type?: string;
  chart_config?: Record<string, any>;
};

export default function Dashboard() {
  const token = localStorage.getItem("token");
  const [me, setMe] = useState<Me | null>(null);
  const [question, setQuestion] = useState("How many rows are there?");
  const [result, setResult] = useState<QueryOut | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [billingMsg, setBillingMsg] = useState<string | null>(null);
  const [showAllRows, setShowAllRows] = useState(false);

  useEffect(() => {
    if (!token) return;
    api<Me>("/me", { token })
      .then(setMe)
      .catch(() => setMe(null));
  }, [token]);

  const kpis = useMemo(() => {
    if (!result?.rows?.length || !result?.columns?.length) return null;
    const yCol = result.columns.find((c) => typeof result.rows[0][c] === "number");
    if (!yCol) return null;
    const values = result.rows
      .map((r) => r[yCol])
      .map((v) => {
        if (v === null || v === undefined) return NaN;
        if (typeof v === "number") return v;
        return Number(v);
      })
      .filter((n) => Number.isFinite(n)) as number[];
    if (!values.length) return null;
    const sum = values.reduce((a, b) => a + b, 0);
    const max = Math.max(...values);
    const min = Math.min(...values);
    const avg = sum / values.length;
    return { rows: result.rows.length, sum, avg, max, min };
  }, [result]);

  const previewRows = useMemo(() => {
    if (!result?.rows?.length) return [];
    if (showAllRows) return result.rows;
    return result.rows.slice(0, 3);
  }, [result, showAllRows]);

  const ChartTooltip = ({ active, payload, label }: any) => {
    if (!active || !payload || !payload.length) return null;
    const pt = payload[0]?.payload || {};
    const raw = payload[0]?.value ?? pt.value;
    const num = typeof raw === "number" ? raw : Number(raw);
    const formatted =
      Number.isFinite(num) && typeof num === "number" ? formatAxisNumber(num) : String(raw ?? "");

    return (
      <div
        style={{
          background: "#141a22",
          border: "1px solid #243044",
          borderRadius: 10,
          padding: "0.55rem 0.7rem",
          boxShadow: "0 14px 40px rgba(0,0,0,0.35)",
          color: "#e8ecf2",
        }}
      >
        <div style={{ color: "#c4b5fd", fontSize: 12, marginBottom: 4 }}>
          {label}
        </div>
        <div style={{ fontWeight: 800, fontSize: 13 }}>
          {formatted}
        </div>
      </div>
    );
  };

  async function upload(f: File) {
    if (!token) return;
    setErr(null);
    const fd = new FormData();
    fd.append("file", f);
    const r = await fetch("/datasets/upload", {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: fd,
    });
    if (!r.ok) {
      const j = await r.json().catch(() => ({}));
      throw new Error((j as { detail?: string }).detail || "Upload failed");
    }
    setBillingMsg(`Uploaded ${f.name}`);
  }

  async function runQuery() {
    if (!token) return;
    setBusy(true);
    setErr(null);
    try {
      const out = await api<QueryOut>("/query", {
        method: "POST",
        token,
        body: JSON.stringify({ question }),
      });
      setShowAllRows(false);
      setResult(out);
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Query failed");
    } finally {
      setBusy(false);
    }
  }

  async function checkout() {
    try {
      setErr(null);
      setBillingMsg("Redirecting to billing page...");
      const s = await api<{ url: string; note?: string }>("/billing/checkout-session", {
        method: "POST",
      });
      const target = s.url?.trim();
      if (!target) {
        throw new Error("Invalid checkout URL returned from server");
      }
      // Use absolute URL if provided, else resolve relative to frontend origin.
      const redirectUrl = target.startsWith("http://") || target.startsWith("https://") ? target : `${window.location.origin}${target}`;
      setBillingMsg(`Redirecting to ${redirectUrl}`);
      // navigate in a tiny delay to allow UI update and confirm behavior
      setTimeout(() => {
        window.location.href = redirectUrl;
      }, 200);
    } catch (e) {
      setBillingMsg(null);
      setErr(e instanceof Error ? e.message : "Billing error");
    }
  }

  if (!token) {
    return (
      <div className="layout">
        <p>Not signed in.</p>
        <Link to="/login">Login</Link>
      </div>
    );
  }

  return (
    <div className="layout">
      <header className="topbar">
        <div className="title">
          <h1>Analytics Workspace</h1>
          <p className="subtitle">
            {me?.workspace?.name || "—"} · {me?.role || "—"} · plan {me?.workspace?.plan || "—"}
          </p>
          <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap", marginTop: "0.25rem" }}>
            <span className="pill">Tenant isolated</span>
            <span className="pill">RBAC: Admin / Analyst / Viewer</span>
            <span className="pill">Text-to-SQL + charts</span>
          </div>
        </div>
        <div className="actions">
          <button className="primary" type="button" onClick={checkout}>
            Upgrade (Stripe demo)
          </button>
          <button
            className="btn"
            type="button"
            onClick={() => {
              localStorage.removeItem("token");
              window.location.href = "/login";
            }}
          >
            Log out
          </button>
        </div>
      </header>

      <div className="dashGrid">
        <div className="dashLeft">
          <div className="card dashCardTight dashCardNoMb">
            <h3 style={{ marginTop: 0, marginBottom: "0.75rem" }}>Chart</h3>
            {!result && (
              <p className="muted" style={{ marginTop: 0 }}>
                Run a query to see a chart + table.
              </p>
            )}
            {result && (
              <>
                <div className="kpis" style={{ marginBottom: "0.9rem" }}>
                  <div className="kpi">
                    <p className="kpiLabel">Rows returned</p>
                    <p className="kpiValue">{formatAxisNumber(result.rows.length)}</p>
                  </div>
                  <div className="kpi">
                    <p className="kpiLabel">Columns</p>
                    <p className="kpiValue">{result.columns.length}</p>
                  </div>
                  <div className="kpi">
                    <p className="kpiLabel">Chart type</p>
                    <p className="kpiValue">{result.chart_type || "auto"}</p>
                  </div>
                  <div className="kpi">
                    <p className="kpiLabel">Status</p>
                    <p className="kpiValue">Ready</p>
                  </div>
                </div>

                <div className="dashChartViz">
                  <ChartRenderer
                    chart_type={result.chart_type || "bar"}
                    chart_config={result.chart_config || {}}
                    rows={result.rows}
                    columns={result.columns}
                  />
                </div>
              </>
            )}
          </div>

          {result && (
            <div className="card dashCardTight dashCardNoMb">
              <h3 style={{ marginTop: 0 }}>Insight</h3>
              <p style={{ marginTop: 0 }}>{result.insight}</p>
              <details style={{ marginTop: "auto" }}>
                <summary>SQL</summary>
                <pre style={{ whiteSpace: "pre-wrap", maxHeight: 120, overflow: "auto" }}>{result.sql}</pre>
              </details>
            </div>
          )}
        </div>

        <div className="dashRight">
          <div className="card dashCardTight dashCardNoMb">
            <h3 style={{ marginTop: 0 }}>Upload CSV</h3>
            <input
              type="file"
              accept=".csv"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) upload(f).catch((ex) => setErr(String(ex)));
              }}
            />
            {billingMsg && <p style={{ color: "#86efac", marginBottom: 0 }}>{billingMsg}</p>}
            <p className="muted" style={{ marginBottom: 0, marginTop: "0.75rem", fontSize: 13 }}>
              Tip: use the generated samples in <code>project-4-fullstack-react-ai-saas/sample-data/</code>.
            </p>
          </div>

          <div className="card dashCardTight dashCardNoMb">
            <h3 style={{ marginTop: 0, marginBottom: "0.5rem" }}>Ask in plain English</h3>
            <p className="muted" style={{ marginTop: 0, marginBottom: "0.75rem", fontSize: 13 }}>
              Try: <code>What was total revenue by region?</code> · <code>Top 5 categories by revenue</code>
            </p>
            <textarea
              className="questionTextarea"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
            />
            <div style={{ marginTop: "0.75rem", display: "flex", gap: "0.6rem", alignItems: "center" }}>
              <button className="primary" type="button" disabled={busy} onClick={runQuery}>
                {busy ? "Running…" : "Run query"}
              </button>
              {err && <span className="error">{err}</span>}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
