export default function DecisionMap({ nodes }) {
  if (!nodes || !nodes.length) {
    return <div>No decision data</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>Decision Map</h3>

      {nodes.map((node) => (
        <div
          key={node.id}
          style={{
            marginTop: "10px",
            padding: "10px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{node.title}</div>
          <div style={{ color: "#9ca3af" }}>{node.type}</div>
        </div>
      ))}
    </div>
  );
}