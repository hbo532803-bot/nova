export default function TaskDependencies({ tasks }) {
  if (!tasks || !tasks.length) {
    return <div>No dependencies</div>;
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
      <h3>Task Dependencies</h3>

      {tasks.map((task) => (
        <div
          key={task.id}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {task.name} → {task.depends_on || "None"}
        </div>
      ))}
    </div>
  );
}