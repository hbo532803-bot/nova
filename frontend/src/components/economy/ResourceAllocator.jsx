export default function ResourceAllocator({ resources }) {
  if (!resources || !resources.length) {
    return <div>No resources</div>;
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
      <h3>Resource Allocation</h3>

      {resources.map((res) => (
        <div
          key={res.name}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {res.name}: {res.value}
        </div>
      ))}
    </div>
  );
}