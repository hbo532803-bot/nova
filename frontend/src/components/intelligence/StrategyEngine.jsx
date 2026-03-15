export default function StrategyEngine({ strategies }) {
  if (!strategies || !strategies.length) {
    return <div>No strategies</div>;
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
      <h3>Strategy Engine</h3>

      {strategies.map((s) => (
        <div
          key={s.id}
          style={{
            padding: "10px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{s.title}</div>
          <div style={{ color: "#9ca3af" }}>
            Confidence: {s.confidence}
          </div>
        </div>
      ))}
    </div>
  );
}