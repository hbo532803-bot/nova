export default function OpportunityActions({ opportunity }) {
  if (!opportunity) return null;

  function runExperiment() {
    console.log("Run experiment", opportunity.id);
  }

  function startExecution() {
    console.log("Start execution", opportunity.id);
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
      <button onClick={runExperiment} style={{ marginRight: "10px" }}>
        Run Experiment
      </button>

      <button onClick={startExecution}>
        Start Execution
      </button>
    </div>
  );
}