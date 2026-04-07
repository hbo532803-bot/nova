import { useMemo } from "react";
import { useNovaStore } from "../../state/novaStore";

export default function ActivityStream() {
  const logs = useNovaStore((s) => s.logs) || [];

  const recentLogs = useMemo(() => logs.slice(0, 20), [logs]);

  return (
    <section
      style={{
        background: "#020617",
        border: "1px solid #1e293b",
        borderRadius: "10px",
        padding: "18px",
        marginBottom: "20px"
      }}
    >
      <h2 style={{ marginTop: 0, marginBottom: "12px" }}>Activity Stream</h2>

      {recentLogs.length === 0 ? (
        <p style={{ opacity: 0.75, margin: 0 }}>No activity yet.</p>
      ) : (
        <div style={{ display: "grid", gap: "10px" }}>
          {recentLogs.map((log, idx) => {
            const message =
              log?.message || log?.event || log?.summary || JSON.stringify(log);

            return (
              <article
                key={`${idx}-${message}`}
                style={{
                  padding: "10px 12px",
                  background: "#0b1220",
                  borderRadius: "8px",
                  border: "1px solid #1e293b"
                }}
              >
                <p style={{ margin: 0, lineHeight: 1.4 }}>{message}</p>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
