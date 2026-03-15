export default function AgentActivityGraph({ activity }) {

  if (!activity || !activity.length) {
    return <div>No activity data</div>;
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
      <h3>Agent Activity</h3>

      {activity.map((a) => (
        <div
          key={a.agent}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {a.agent} : {a.tasks} tasks
        </div>
      ))}
    </div>
  );
}