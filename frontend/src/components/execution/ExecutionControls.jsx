import { startExecution, stopExecution } from "../../services/executionApi";

export default function ExecutionControls({ executionId }) {

  async function start() {
    await startExecution(executionId);
  }

  async function stop() {
    await stopExecution(executionId);
  }

  return (
    <div
      style={{
        marginTop: "15px"
      }}
    >
      <button
        onClick={start}
        style={{ marginRight: "10px" }}
      >
        Start Execution
      </button>

      <button onClick={stop}>
        Stop Execution
      </button>
    </div>
  );
}