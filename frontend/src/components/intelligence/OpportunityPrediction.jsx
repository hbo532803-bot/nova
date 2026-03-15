export default function OpportunityPrediction({ predictions }) {
  if (!predictions || !predictions.length) {
    return <div>No predictions</div>;
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
      <h3>Opportunity Predictions</h3>

      {predictions.map((p) => (
        <div
          key={p.id}
          style={{
            padding: "10px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{p.market}</div>
          <div style={{ color: "#9ca3af" }}>
            Probability: {p.probability}
          </div>
        </div>
      ))}
    </div>
  );
}