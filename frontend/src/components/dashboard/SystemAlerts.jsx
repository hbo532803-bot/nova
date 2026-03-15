export default function SystemAlerts({ alerts }) {
  if (!alerts || !alerts.length) {
    return <div>No alerts</div>;
  }

  return (
    <div
      style={{
        marginTop: "20px",
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>System Alerts</h3>

      {alerts.map((a) => (
        <div
          key={a.id}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{a.message}</div>
          <div style={{ color: "#9ca3af" }}>
            Level: {a.level}
          </div>
        </div>
      ))}
    </div>
  );
}