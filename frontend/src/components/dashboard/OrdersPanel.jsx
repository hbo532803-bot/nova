import { useMemo } from "react";
import { useNovaStore } from "../../state/novaStore";

export default function OrdersPanel() {
  const commands = useNovaStore((s) => s.commands) || [];

  const rows = useMemo(() => commands.slice(0, 8), [commands]);

  return (
    <section className="admin-card">
      <h3>Orders List</h3>
      <p className="admin-subtext">Live queue derived from active command/order pipeline.</p>
      <div className="admin-table-wrap">
        <table className="admin-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Command</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.id}>
                <td>{row.id}</td>
                <td>{row.command_text}</td>
                <td>{row.status}</td>
                <td>{row.created_at}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={4}>No orders yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}
