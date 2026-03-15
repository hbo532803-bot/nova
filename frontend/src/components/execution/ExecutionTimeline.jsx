export default function ExecutionTimeline({ timeline }) {
  if (!timeline || !timeline.length) {
    return <div>No timeline</div>;
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
      <h3>Execution Timeline</h3>

      {timeline.map((item, i) => (
        <div
          key={i}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{item.event}</div>
          <div style={{ color: "#9ca3af" }}>
            {item.time}
          </div>
        </div>
      ))}
    </div>
  );
}