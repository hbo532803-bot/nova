import React, { useState, useEffect } from "react";
import {
  LineChart, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, ResponsiveContainer
} from "recharts";

const API_BASE = "http://127.0.0.1:8000/api";

export default function App() {

  const [token, setToken] = useState(localStorage.getItem("token"));
  const [dashboard, setDashboard] = useState(null);
  const [chartData, setChartData] = useState([]);
  const [logs, setLogs] = useState([]);

  /* LOGIN */
  const login = async () => {
    const form = new URLSearchParams();
    form.append("username", "admin");
    form.append("password", "admin123");

    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form
    });

    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
    }
  };

  /* LOAD DASHBOARD */
  const loadDashboard = async () => {
    const res = await fetch(`${API_BASE}/nova/dashboard`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    if (!res.ok) return;

    const data = await res.json();
    setDashboard(data);

    setChartData(prev => [
      ...prev.slice(-30),
      {
        time: new Date().toLocaleTimeString(),
        profit: data.system.net_profit,
        confidence: data.system.confidence.score
      }
    ]);

    setLogs(prev => [
      ...prev.slice(-30),
      `[${new Date().toLocaleTimeString()}] System stable`
    ]);
  };

  useEffect(() => {
    if (token) {
      loadDashboard();
      const interval = setInterval(loadDashboard, 8000);
      return () => clearInterval(interval);
    }
  }, [token]);

  if (!token) {
    return (
      <div style={styles.center}>
        <button style={styles.loginBtn} onClick={login}>
          ENTER NOVA CONTROL
        </button>
      </div>
    );
  }

  if (!dashboard) return <div style={styles.center}>Initializing Nova...</div>;

  const { system, experiments, agents, risk } = dashboard;

  const budgetPercent = Math.min(100, (risk.tokens_today / 100000) * 100);

  return (
    <div style={styles.container}>

      {/* TOP BAR */}
      <div style={styles.topBar}>
        <div>NOVA AI LAB</div>
        <div style={{
          color: risk.emergency_active ? "#ff0044" : "#00ffcc"
        }}>
          {risk.emergency_active ? "EMERGENCY ACTIVE" : "SYSTEM NORMAL"}
        </div>
      </div>

      {/* KPI STRIP */}
      <div style={styles.kpiRow}>
        <KPI label="NET PROFIT" value={system.net_profit} />
        <KPI label="CONFIDENCE" value={system.confidence.score} />
        <KPI label="ACTIVE" value={risk.active_experiments} />
        <KPI label="SCALING" value={risk.scaling_experiments} />
      </div>

      {/* MAIN GRID */}
      <div style={styles.mainGrid}>

        {/* Graph */}
        <div style={styles.card}>
          <h3>ECONOMIC SIGNAL MATRIX</h3>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartData}>
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="time" stroke="#777" />
              <YAxis stroke="#777" />
              <Tooltip />
              <Line type="monotone" dataKey="profit" stroke="#00ffcc" strokeWidth={3} />
              <Line type="monotone" dataKey="confidence" stroke="#ff00ff" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Risk Panel */}
        <div style={styles.card}>
          <h3>RISK MONITOR</h3>
          <Stat label="API CALLS" value={risk.api_calls_today} />
          <Stat label="TOKENS" value={risk.tokens_today} />
          <Stat label="FAILED" value={risk.failed_experiments} danger={risk.failed_experiments > 2} />
          <Stat label="REFLECTIONS" value={risk.reflection_entries} />

          <div style={{ marginTop: "15px" }}>
            <div style={styles.progressOuter}>
              <div style={{
                ...styles.progressInner,
                width: `${budgetPercent}%`
              }} />
            </div>
          </div>
        </div>

      </div>

      {/* EXPERIMENT TABLE */}
      <Table title="EXPERIMENT MATRIX" data={experiments} />

      {/* AGENTS */}
      <Table title="AGENT NETWORK" data={agents} />

      {/* LOGS */}
      <div style={styles.card}>
        <h3>LIVE SYSTEM LOG</h3>
        <div style={styles.logBox}>
          {logs.map((log, i) => (
            <div key={i}>{log}</div>
          ))}
        </div>
        <div style={styles.controlRow}>
          <button onClick={() => loadDashboard()}>Run Cycle</button>
          <button>Emergency Stop</button>
          <button onClick={() => {
            localStorage.removeItem("token");
            setToken(null);
          }}>Logout</button>
        </div>
      </div>

    </div>
  );
}

/* COMPONENTS */

function KPI({ label, value }) {
  return (
    <div style={styles.kpiCard}>
      <div style={styles.kpiLabel}>{label}</div>
      <div style={styles.kpiValue}>{value}</div>
    </div>
  );
}

function Stat({ label, value, danger }) {
  return (
    <div style={{
      ...styles.statRow,
      color: danger ? "#ff0044" : "#ccc"
    }}>
      <span>{label}</span>
      <span>{value}</span>
    </div>
  );
}

function Table({ title, data }) {
  if (!data || data.length === 0) return null;

  return (
    <div style={styles.card}>
      <h3>{title}</h3>
      <table style={styles.table}>
        <thead>
          <tr>
            {Object.keys(data[0]).map(k => <th key={k}>{k}</th>)}
          </tr>
        </thead>
        <tbody>
          {data.map((row, i) => (
            <tr key={i} style={{
              backgroundColor:
                row.status === "FAILED"
                  ? "#2a0000"
                  : row.status === "SCALING"
                  ? "#002a1a"
                  : "transparent"
            }}>
              {Object.values(row).map((v, idx) => (
                <td key={idx}>{String(v)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* STYLES */

const styles = {
  container: {
    background: "linear-gradient(135deg,#050510,#0a0a1f)",
    minHeight: "100vh",
    padding: "30px",
    color: "#eee",
    fontFamily: "Orbitron, sans-serif"
  },
  topBar: {
    display: "flex",
    justifyContent: "space-between",
    marginBottom: "20px",
    fontSize: "18px",
    letterSpacing: "2px",
    color: "#00ffcc"
  },
  kpiRow: {
    display: "flex",
    gap: "15px",
    marginBottom: "25px"
  },
  kpiCard: {
    flex: 1,
    background: "rgba(20,20,40,0.6)",
    padding: "15px",
    borderRadius: "10px",
    backdropFilter: "blur(8px)"
  },
  kpiLabel: { fontSize: "11px", opacity: 0.6 },
  kpiValue: { fontSize: "20px", marginTop: "5px" },
  mainGrid: {
    display: "grid",
    gridTemplateColumns: "2fr 1fr",
    gap: "20px",
    marginBottom: "25px"
  },
  card: {
    background: "rgba(20,20,40,0.6)",
    padding: "20px",
    borderRadius: "12px",
    backdropFilter: "blur(12px)",
    marginBottom: "20px"
  },
  statRow: {
    display: "flex",
    justifyContent: "space-between",
    padding: "6px 0"
  },
  table: {
    width: "100%",
    borderCollapse: "collapse"
  },
  logBox: {
    height: "120px",
    overflowY: "auto",
    background: "#000",
    padding: "10px",
    fontSize: "12px"
  },
  controlRow: {
    display: "flex",
    gap: "10px",
    marginTop: "10px"
  },
  progressOuter: {
    width: "100%",
    height: "12px",
    backgroundColor: "#222",
    borderRadius: "6px"
  },
  progressInner: {
    height: "100%",
    background: "linear-gradient(90deg,#00ffcc,#ff00ff)",
    borderRadius: "6px"
  },
  center: {
    height: "100vh",
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    background: "#050510"
  },
  loginBtn: {
    padding: "15px 40px",
    fontSize: "16px",
    background: "linear-gradient(90deg,#00ffcc,#ff00ff)",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    color: "#000"
  }
};