export default function PatternDetector({ patterns }) {
  if (!patterns || !patterns.length) {
    return <div>No patterns detected</div>;
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
      <h3>Detected Patterns</h3>

      {patterns.map((p) => (
        <div
          key={p.id}
          style={{
            padding: "10px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{p.name}</div>
          <div style={{ color: "#9ca3af" }}>
            Score: {p.score}
          </div>
        </div>
      ))}
    </div>
  );
}