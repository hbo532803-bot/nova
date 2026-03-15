import { runExperiment, stopExperiment } from "../../services/experimentApi";

export default function ExperimentControl({ experiment }) {

  if (!experiment) return null;

  async function run() {
    await runExperiment({ id: experiment.id });
  }

  async function stop() {
    await stopExperiment(experiment.id);
  }

  return (
    <div
      style={{
        marginTop: "15px"
      }}
    >
      <button
        onClick={run}
        style={{ marginRight: "10px" }}
      >
        Run
      </button>

      <button onClick={stop}>
        Stop
      </button>
    </div>
  );
}