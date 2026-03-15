export default function ExecutionPlan({ plan }) {
  if (!plan || !plan.length) {
    return <div>No execution plan available</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>Execution Plan</h3>

      <div style={{ marginTop: "15px" }}>
        {plan.map((step, index) => (
          <div
            key={index}
            style={{
              padding: "10px",
              borderBottom: "1px solid #374151"
            }}
          >
            <div>Step {index + 1}</div>
            <div>{step.task}</div>
          </div>
        ))}
      </div>
    </div>
  );
}