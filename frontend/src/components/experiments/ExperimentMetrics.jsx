export default function ExperimentMetrics({ metrics }) {
  if (!metrics) {
    return <div>No metrics</div>;
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
      <h3>Experiment Metrics</h3>

      <div style={{ marginTop: "10px" }}>
        <p>Visitors: {metrics.visitors}</p>
        <p>Conversions: {metrics.conversions}</p>
        <p>Conversion Rate: {metrics.rate}</p>
      </div>
    </div>
  );
}