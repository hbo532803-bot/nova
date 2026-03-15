import MainLayout from "../components/layout/MainLayout";
import ProfitEngine from "../components/economy/ProfitEngine";
import ResourceAllocator from "../components/economy/ResourceAllocator";

const demoProfit = {
  revenue: "$12,000",
  cost: "$4,000",
  profit: "$8,000"
};

const demoResources = [
  { name: "Compute", value: "70%" },
  { name: "Agents", value: "12 active" },
  { name: "Experiments", value: "3 running" }
];

export default function EconomyPage() {
  return (
    <MainLayout>
      <h1>Economy Engine</h1>

      <ProfitEngine data={demoProfit} />

      <ResourceAllocator resources={demoResources} />
    </MainLayout>
  );
}