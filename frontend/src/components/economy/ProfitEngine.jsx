export default function ProfitEngine({ data }) {
  if (!data) {
    return <div>No profit data</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>Profit Engine</h3>

      <div style={{ marginTop: "10px" }}>
        <p>Total Revenue: {data.revenue}</p>
        <p>Total Cost: {data.cost}</p>
        <p>Net Profit: {data.profit}</p>
      </div>
    </div>
  );
}