import { useNovaStore } from "../../state/novaStore";

export default function ConfidencePanel() {
  const confidence = useNovaStore((s) => s.confidence);
  const reflections = useNovaStore((s) => s.reflections) || [];
  const recent = reflections.slice(0, 5);

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
      <h2 style={{ marginTop: 0 }}>Confidence / Learning</h2>
      <div style={{ display: "flex", gap: "20px", flexWrap: "wrap" }}>
        <Metric title="Confidence score" value={confidence?.score ?? "-"} />
        <Metric title="Autonomy" value={confidence?.autonomy ?? "-"} />
      </div>
      <p style={{ opacity: 0.7, marginTop: "12px", marginBottom: 0 }}>
        Confidence is adjusted automatically based on action reflections.
      </p>

      <div style={{ marginTop: "14px" }}>
        <h3 style={{ marginBottom: 8 }}>Recent reflections</h3>
        {recent.length === 0 ? (
          <p style={{ opacity: 0.7 }}>No reflections recorded yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ textAlign: "left", opacity: 0.8 }}>
                  <th style={th}>When</th>
                  <th style={th}>Objective</th>
                  <th style={th}>Success</th>
                </tr>
              </thead>
              <tbody>
                {recent.map((r) => (
                  <tr key={r.id} style={{ borderTop: "1px solid #1e293b" }}>
                    <td style={td}>{r.created_at}</td>
                    <td style={td}>{r.input_objective}</td>
                    <td style={td}>{r.success ? "YES" : "NO"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Metric({ title, value }) {
  return (
    <div
      style={{
        background: "#0b1220",
        padding: "12px 14px",
        borderRadius: "10px",
        border: "1px solid #1e293b",
        minWidth: "220px"
      }}
    >
      <div style={{ opacity: 0.7, fontSize: 12 }}>{title}</div>
      <div style={{ fontSize: 22, fontWeight: 700 }}>{value}</div>
    </div>
  );
}

const th = { padding: "8px 8px" };
const td = { padding: "10px 8px", verticalAlign: "top" };

