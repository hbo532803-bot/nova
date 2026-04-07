import { useMemo } from "react";
import { useNovaStore } from "../../state/novaStore";

export default function BusinessMetricsPanel() {
  const opportunities = useNovaStore((s) => s.opportunities) || [];
  const portfolio = useNovaStore((s) => s.portfolioHealth) || {};

  const leadCount = opportunities.reduce((acc, item) => acc + Number(item?.leads || 0), 0);
  const revenue = Number(portfolio?.summary?.estimated_revenue || 0);
  const successRate = Number(portfolio?.summary?.success_rate || 0);

  const stats = useMemo(
    () => [
      { label: "Leads", value: leadCount },
      { label: "Revenue", value: `$${revenue.toLocaleString()}` },
      { label: "Success Rate", value: `${successRate}%` }
    ],
    [leadCount, revenue, successRate]
  );

  return (
    <section className="admin-card">
      <h3>Metrics</h3>
      <div className="admin-metric-grid">
        {stats.map((stat) => (
          <article key={stat.label} className="admin-metric-item">
            <p>{stat.label}</p>
            <h4>{stat.value}</h4>
          </article>
        ))}
      </div>
    </section>
  );
}
