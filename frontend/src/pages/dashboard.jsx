import MainLayout from "../components/layout/MainLayout";
import useNovaSystem from "../hooks/useNovaSystem";

import SystemMetrics from "../components/dashboard/SystemMetrics";
import ActivityStream from "../components/logs/ActivityStream";
import SwarmControl from "../components/agents/SwarmControl";

export default function Dashboard(){

  useNovaSystem();

  return(

    <MainLayout>

      <SystemMetrics />

      <SwarmControl />

      <ActivityStream />

    </MainLayout>

  )

}