import { startAgent, stopAgent } from "../../services/agentApi";

export default function AgentControl({ agent }) {
  if (!agent) return null;

  async function start() {
    await startAgent(agent.id);
  }

  async function stop() {
    await stopAgent(agent.id);
  }

  return (
    <div style={{ marginTop: "10px" }}>
      <button onClick={start} style={{ marginRight: "10px" }}>
        Start
      </button>

      <button onClick={stop}>
        Stop
      </button>
    </div>
  );
}