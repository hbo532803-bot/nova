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

export default function Dashboard(){

  useNovaSystem();
  useEventBus();

  return(

    <MainLayout>

      <SystemStatePanel />

      <ConfidencePanel />

      <IntelligencePanel />

      <SwarmControl />

      <CommandHistoryPanel />

      <ActivityStream />

    </MainLayout>

  )

}