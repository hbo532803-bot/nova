export default function LiveSignalFeed({ signals }) {
  if (!signals || !signals.length) {
    return <div>No signals</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px",
        marginTop: "20px"
      }}
    >
      <h3>Live Signals</h3>

      {signals.map((s) => (
        <div
          key={s.id}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{s.source}</div>
          <div style={{ color: "#9ca3af" }}>
            {s.signal}
          </div>
        </div>
      ))}
    </div>
  );
}