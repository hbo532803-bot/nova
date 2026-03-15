export default function AgentNetworkGraph({ links }) {
  if (!links || !links.length) {
    return <div>No network data</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px",
        marginTop: "20px"
      }}
    >
      <h3>Agent Network</h3>

      {links.map((link, index) => (
        <div
          key={index}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {link.source} → {link.target}
        </div>
      ))}
    </div>
  );
}