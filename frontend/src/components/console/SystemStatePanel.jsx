import { useNovaStore } from "../../state/novaStore";
import { marketScan } from "../../services/consoleApi";

export default function SystemStatePanel() {
  const systemState = useNovaStore((s) => s.systemState);

  async function scan() {
    try {
      await marketScan();
      alert("Market scan queued");
    } catch (e) {
      console.error(e);
      alert("Failed to queue market scan");
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
      <div style={{ display: "flex", justifyContent: "space-between", gap: "12px" }}>
        <div>
          <h2 style={{ margin: 0 }}>System State</h2>
          <p style={{ opacity: 0.8, marginTop: 6, marginBottom: 0 }}>
            State: <b>{systemState?.state || "UNKNOWN"}</b>
          </p>
          <p style={{ opacity: 0.6, marginTop: 6, marginBottom: 0 }}>
            Updated: {systemState?.updated_at || "-"}
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <button
            onClick={scan}
            style={{
              padding: "8px 14px",
              background: "#9333ea",
              border: "none",
              color: "white",
              borderRadius: "6px",
              cursor: "pointer"
            }}
          >
            Queue Market Scan
          </button>
        </div>
      </div>
    </div>
  );
}

