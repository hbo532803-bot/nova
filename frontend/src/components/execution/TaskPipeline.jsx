export default function TaskPipeline({ tasks }) {
  if (!tasks || !tasks.length) {
    return <div>No tasks in pipeline</div>;
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
      <h3>Task Pipeline</h3>

      {tasks.map((task) => (
        <div
          key={task.id}
          style={{
            padding: "10px",
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