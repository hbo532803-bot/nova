export default function ExecutionFlowGraph({ steps }) {

  if (!steps || !steps.length) {
    return <div>No flow data</div>;
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
      <h3>Execution Flow</h3>

      {steps.map((s, i) => (
        <div
          key={i}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {s.from} → {s.to}
        </div>
      ))}
    </div>
  );
}