import MainLayout from "../components/layout/MainLayout";
import AgentSwarmView from "../components/swarm/AgentSwarmView";
import AgentNetworkGraph from "../components/swarm/AgentNetworkGraph";

const demoAgents = [
  { id: 1, name: "Research Agent", status: "active" },
  { id: 2, name: "Execution Agent", status: "active" },
  { id: 3, name: "Marketing Agent", status: "idle" },
  { id: 4, name: "Data Agent", status: "active" }
];

const demoLinks = [
  { source: "Research Agent", target: "Execution Agent" },
  { source: "Execution Agent", target: "Marketing Agent" },
  { source: "Data Agent", target: "Research Agent" }
];

export default function SwarmPage() {
  return (
    <MainLayout>
      <h1>Agent Swarm</h1>

      <AgentSwarmView agents={demoAgents} />

      <AgentNetworkGraph links={demoLinks} />
    </MainLayout>
  );
}