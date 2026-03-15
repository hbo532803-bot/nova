export default function SystemGraph({ nodes }) {
  if (!nodes || !nodes.length) {
    return <div>No graph data</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>System Graph</h3>

      {nodes.map((node) => (
        <div
          key={node.id}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {node.label}
        </div>
      ))}
    </div>
  );
}