import MainLayout from "../components/layout/MainLayout";
import DecisionMap from "../components/intelligence/DecisionMap";

const demoNodes = [
  { id: 1, title: "Market Signal", type: "signal" },
  { id: 2, title: "Opportunity Detected", type: "analysis" },
  { id: 3, title: "Strategy Generated", type: "strategy" }
];

export default function IntelligencePage() {
  return (
    <MainLayout>
      <h1>Intelligence</h1>

      <DecisionMap nodes={demoNodes} />
    </MainLayout>
  );
}