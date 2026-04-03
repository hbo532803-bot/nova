import { useNovaStore } from "../../state/novaStore";
import { submitCommand } from "../../services/consoleApi";
import { useState } from "react";

export default function CommandHistoryPanel() {
  const commands = useNovaStore((s) => s.commands) || [];
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function run() {
    const t = text.trim();
    if (!t) return;
    setSubmitting(true);
    try {
      await submitCommand(t);
      setText("");
    } catch (e) {
      console.error(e);
      alert("Failed to submit command");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      style={{
        background: "#020617",
        padding: "20px",
        borderRadius: "10px",
        border: "1px solid #1e293b",
        marginBottom: "20px"
      }}
    >
      <h2 style={{ marginTop: 0 }}>Command Interface</h2>

      <div style={{ display: "flex", gap: "10px", marginBottom: "14px" }}>
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder='Try: "analyze market", "expand experiments", "run experiment 1", "opportunity convert 3"'
          style={{
            flex: 1,
            padding: "10px 12px",
            background: "#0b1220",
            border: "1px solid #1e293b",
            color: "white",
            borderRadius: "8px"
          }}
          onKeyDown={(e) => {
            if (e.key === "Enter") run();
          }}
        />
        <button
          onClick={run}
          disabled={submitting}
          style={{
            padding: "10px 14px",
            background: submitting ? "#334155" : "#2563eb",
            border: "none",
            color: "white",
            borderRadius: "8px",
            cursor: submitting ? "not-allowed" : "pointer"
          }}
        >
          Queue
        </button>
      </div>

      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", opacity: 0.8 }}>
              <th style={th}>ID</th>
              <th style={th}>Command</th>
              <th style={th}>Status</th>
              <th style={th}>Created</th>
            </tr>
          </thead>
          <tbody>
            {commands.map((c) => (
              <tr key={c.id} style={{ borderTop: "1px solid #1e293b" }}>
                <td style={td}>{c.id}</td>
                <td style={td}>{c.command_text}</td>
                <td style={td}>
                  <span style={{ fontWeight: 700 }}>{c.status}</span>
                </td>
                <td style={td}>{c.created_at}</td>
              </tr>
            ))}
            {commands.length === 0 && (
              <tr>
                <td style={td} colSpan={4}>
                  No command history yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const th = { padding: "8px 8px" };
const td = { padding: "10px 8px", verticalAlign: "top" };

