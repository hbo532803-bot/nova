export default function OpportunityDetails({ opportunity }) {
  if (!opportunity) {
    return <div>Select opportunity</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>{opportunity.title}</h3>

      <div style={{ marginTop: "10px" }}>
        <p>Market: {opportunity.market}</p>
        <p>Score: {opportunity.score}</p>
        <p>Risk: {opportunity.risk}</p>
        <p>ROI: {opportunity.roi}</p>
      </div>
    </div>
  );
}