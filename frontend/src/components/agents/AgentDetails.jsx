import AgentStatus from "./AgentStatus";
import AgentControl from "./AgentControl";

export default function AgentDetails({ agent }) {
  if (!agent) {
    return <div>Select an agent</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>{agent.name}</h3>

      <AgentStatus agent={agent} />

      <AgentControl agent={agent} />
    </div>
  );
}