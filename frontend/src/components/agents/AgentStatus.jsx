export default function AgentStatus({ agent }) {
  if (!agent) return null;

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "15px",
        borderRadius: "6px"
      }}
    >
      <div>Name: {agent.name}</div>
      <div>Status: {agent.status}</div>
      <div>Tasks: {agent.tasks}</div>
    </div>
  );
}