export function buildExecutionGraph(tasks) {
  return tasks.map((task) => ({
    id: task.id,
    label: task.name,
    status: task.status
  }));
}