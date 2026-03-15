export default function DataFlowGraph({ flows }) {

  if (!flows || !flows.length) {
    return <div>No data flows</div>;
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
      <h3>Data Flow</h3>

      {flows.map((f, i) => (
        <div
          key={i}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {f.source} → {f.target}
        </div>
      ))}
    </div>
  );
}