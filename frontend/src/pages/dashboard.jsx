import MainLayout from "../components/layout/MainLayout";
import useNovaSystem from "../hooks/useNovaSystem";
import useEventBus from "../hooks/useEventBus";

import SystemMetrics from "../components/dashboard/SystemMetrics";
import ActivityStream from "../components/logs/ActivityStream";
import SwarmControl from "../components/agents/SwarmControl";
import CommandHistoryPanel from "../components/console/CommandHistoryPanel";
import SystemStatePanel from "../components/console/SystemStatePanel";
import ConfidencePanel from "../components/console/ConfidencePanel";
import IntelligencePanel from "../components/console/IntelligencePanel";
import OrdersPanel from "../components/dashboard/OrdersPanel";
import BusinessMetricsPanel from "../components/dashboard/BusinessMetricsPanel";
import "../styles/admin.css";

export default function Dashboard() {
  useNovaSystem();
  useEventBus();

  return (
    <MainLayout>
      <div className="admin-page">
        <SystemMetrics />

        <div className="admin-grid">
          <SystemStatePanel />
          <BusinessMetricsPanel />
        </div>

        <OrdersPanel />

        <CommandHistoryPanel />
        <ConfidencePanel />
        <IntelligencePanel />
        <SwarmControl />
        <ActivityStream />
      </div>
    </MainLayout>
  );
}
