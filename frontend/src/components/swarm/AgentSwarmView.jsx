import { useEffect, useState } from "react";

export default function AgentSwarmView({ agents }) {
  const [nodes, setNodes] = useState([]);

  useEffect(() => {
    if (agents) {
      setNodes(agents);
    }
  }, [agents]);

  if (!nodes || !nodes.length) {
    return <div>No swarm agents</div>;
  }

  return (
    <div
      style={{
        background: "#1f2937",
        padding: "20px",
        borderRadius: "8px"
      }}
    >
      <h3>Agent Swarm</h3>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4,1fr)",
          gap: "10px",
          marginTop: "15px"
        }}
      >
        {nodes.map((agent) => (
          <div
            key={agent.id}
            style={{
              background: "#111827",
              padding: "15px",
              borderRadius: "6px"
            }}
          >
            <div>{agent.name}</div>
            <div>Status: {agent.status}</div>
          </div>
        ))}
      </div>
    </div>
  );
}