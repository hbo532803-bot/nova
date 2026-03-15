export default function ExperimentRunner({ experiments }) {
  if (!experiments || !experiments.length) {
    return <div>No experiments running</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>Experiments</h3>

      {experiments.map((exp) => (
        <div
          key={exp.id}
          style={{
            padding: "10px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{exp.name}</div>
          <div>Status: {exp.status}</div>
        </div>
      ))}
    </div>
  );
}