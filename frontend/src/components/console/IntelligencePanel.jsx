import { useMemo, useState } from "react";
import { useNovaStore } from "../../state/novaStore";
import { attachPlaybook, strategyLearn, recoverSystem, evolveAgents } from "../../services/consoleApi";

export default function IntelligencePanel() {
  const playbooks = useNovaStore((s) => s.playbooks) || {};
  const experiments = useNovaStore((s) => s.experiments) || [];
  const analytics = useNovaStore((s) => s.experimentAnalytics) || {};
  const activity = useNovaStore((s) => s.agentActivity) || [];
  const trend = useNovaStore((s) => s.confidenceTrend) || [];
  const stability = useNovaStore((s) => s.stabilityHealth) || {};
  const productivity = useNovaStore((s) => s.agentProductivity) || [];
  const kg = useNovaStore((s) => s.knowledgeGraph) || {};
  const portfolio = useNovaStore((s) => s.portfolioHealth) || {};
  const strategy = useNovaStore((s) => s.currentStrategy) || {};
  const kgInsights = useNovaStore((s) => s.knowledgeInsights) || {};
  const cognitive = useNovaStore((s) => s.cognitiveLast) || {};
  const research = useNovaStore((s) => s.researchLast) || {};

  const [expId, setExpId] = useState(experiments?.[0]?.id || "");
  const playbookNames = useMemo(() => Object.keys(playbooks || {}), [playbooks]);
  const [playbookName, setPlaybookName] = useState(playbookNames?.[0] || "");
  const [busy, setBusy] = useState(false);

  async function onAttach() {
    if (!expId || !playbookName) return;
    setBusy(true);
    try {
      await attachPlaybook(expId, playbookName);
    } finally {
      setBusy(false);
    }
  }

  async function onLearn() {
    setBusy(true);
    try {
      await strategyLearn();
    } finally {
      setBusy(false);
    }
  }

  async function onRecover() {
    setBusy(true);
    try {
      await recoverSystem();
    } finally {
      setBusy(false);
    }
  }

  async function onEvolveAgents() {
    setBusy(true);
    try {
      await evolveAgents();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card">
      <h3>System Intelligence</h3>

      <div style={{ display: "grid", gap: 8 }}>
        <div>
          <strong>Stability</strong>
          <div style={{ fontSize: 14, opacity: 0.9 }}>
            OK: {String(!!stability?.ok)} | State: {stability?.state?.state || "—"} | Stuck running:{" "}
            {(stability?.stuck_commands || []).length}
          </div>
          <button disabled={busy} onClick={onRecover}>
            Recover system
          </button>
          <button disabled={busy} onClick={onEvolveAgents}>
            Evolve agents
          </button>
        </div>

        <div>
          <strong>Experiment analytics</strong>
          <div style={{ fontSize: 14, opacity: 0.9 }}>
            Experiments: {analytics?.summary?.experiments ?? 0} | Success rate:{" "}
            {analytics?.summary?.success_rate ?? 0} | Avg ROI: {analytics?.summary?.avg_roi ?? 0} | Trend:{" "}
            {analytics?.summary?.trend ?? "flat"}
          </div>
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
          <strong>Attach playbook</strong>
          <select value={expId} onChange={(e) => setExpId(e.target.value)}>
            {experiments.map((e) => (
              <option key={e.id} value={e.id}>
                {e.id} — {e.name}
              </option>
            ))}
          </select>
          <select value={playbookName} onChange={(e) => setPlaybookName(e.target.value)}>
            {playbookNames.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
          <button disabled={busy} onClick={onAttach}>
            Attach
          </button>
          <button disabled={busy} onClick={onLearn}>
            Learn strategy
          </button>
        </div>

        <div>
          <strong>Recent experiments</strong>
          <div style={{ maxHeight: 220, overflow: "auto" }}>
            <table style={{ width: "100%", fontSize: 13 }}>
              <thead>
                <tr>
                  <th align="left">ID</th>
                  <th align="left">Status</th>
                  <th align="left">Validation</th>
                  <th align="left">ROI</th>
                  <th align="left">Success score</th>
                </tr>
              </thead>
              <tbody>
                {(analytics?.experiments || []).slice(0, 10).map((e) => (
                  <tr key={e.id}>
                    <td>{e.id}</td>
                    <td>{e.status}</td>
                    <td>{e.validation_score}</td>
                    <td>{e.roi}</td>
                    <td>{e.success_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <strong>Agent activity (latest)</strong>
          <div style={{ maxHeight: 180, overflow: "auto", fontSize: 13 }}>
            <table style={{ width: "100%" }}>
              <thead>
                <tr>
                  <th align="left">Agent</th>
                  <th align="left">Action</th>
                  <th align="left">Result</th>
                  <th align="left">At</th>
                </tr>
              </thead>
              <tbody>
                {activity.slice(0, 15).map((e, i) => (
                  <tr key={i}>
                    <td>{e.agent_name}</td>
                    <td>{e.action}</td>
                    <td>{String(e.result || "").slice(0, 40)}</td>
                    <td>{String(e.created_at || "")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <strong>Confidence trend</strong>
          <div style={{ fontSize: 13, opacity: 0.9 }}>
            Latest: {trend?.[trend.length - 1]?.confidence_after ?? "—"} | Points: {trend.length}
          </div>
          <div style={{ maxHeight: 120, overflow: "auto", fontSize: 12 }}>
            {(trend || []).slice(-10).map((p) => (
              <div key={p.id}>
                {p.created_at}: {p.confidence_before} → {p.confidence_after} (success={String(!!p.success)})
              </div>
            ))}
          </div>
        </div>

        <div>
          <strong>Agent productivity (7d)</strong>
          <div style={{ fontSize: 13, opacity: 0.9 }}>
            {productivity.slice(0, 6).map((a) => `${a.agent_name}:${a.actions}`).join(" | ") || "—"}
          </div>
        </div>

        <div>
          <strong>Knowledge graph</strong>
          <div style={{ fontSize: 13, opacity: 0.9 }}>
            Nodes: {kg?.nodes ?? 0} | Edges: {kg?.edges ?? 0}
          </div>
        </div>

        <div>
          <strong>Portfolio health</strong>
          <div style={{ fontSize: 13, opacity: 0.9 }}>
            Trend: {portfolio?.summary?.trend || "—"} | Success rate: {portfolio?.summary?.success_rate ?? "—"}
          </div>
        </div>

        <div>
          <strong>Strategy signals</strong>
          <div style={{ fontSize: 12, opacity: 0.9 }}>
            {JSON.stringify((strategy?.strategy?.adjustments || []).slice(0, 4))}
          </div>
        </div>

        <div>
          <strong>KG insights</strong>
          <div style={{ fontSize: 13, opacity: 0.9 }}>
            Outcomes: {JSON.stringify(kgInsights?.outcome_counts || {})}
          </div>
          <div style={{ fontSize: 12, opacity: 0.9 }}>
            Reusable: {JSON.stringify((kgInsights?.reusable_strategies || [])[0] || {})}
          </div>
          <div style={{ fontSize: 12, opacity: 0.9 }}>
            History: {JSON.stringify(kgInsights?.experiment_history_patterns || {})}
          </div>
        </div>

        <div>
          <strong>Cognitive loop</strong>
          <div style={{ fontSize: 12, opacity: 0.9 }}>
            {JSON.stringify(cognitive?.cognitive?.reason || {})}
          </div>
        </div>

        <div>
          <strong>Research signals</strong>
          <div style={{ fontSize: 12, opacity: 0.9 }}>
            Proposals: {(research?.research?.proposals || []).length} | Competitors: {(research?.research?.competitors || []).length}
          </div>
        </div>
      </div>
    </div>
  );
}

