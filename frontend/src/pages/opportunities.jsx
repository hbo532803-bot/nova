import MainLayout from "../components/layout/MainLayout";
import OpportunityList from "../components/opportunities/OpportunityList";
import DiscoveryControl from "../components/opportunities/DiscoveryControl";
import useNovaSystem from "../hooks/useNovaSystem";

export default function Opportunities(){

  useNovaSystem();

  return(

    <MainLayout>

      <h1>Opportunities</h1>

      <DiscoveryControl />

      <OpportunityList />

    </MainLayout>

  )

}