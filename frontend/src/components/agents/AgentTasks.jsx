export default function AgentTasks({ tasks }) {
  if (!tasks || !tasks.length) {
    return <div>No tasks</div>;
  }

  return (
    <div
      style={{
        marginTop: "15px",
        background: "#1f2937",
        padding: "15px",
        borderRadius: "8px"
      }}
    >
      <h4>Agent Tasks</h4>

      {tasks.map((task) => (
        <div
          key={task.id}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          <div>{task.name}</div>
          <div>Status: {task.status}</div>
        </div>
      ))}
    </div>
  );
}