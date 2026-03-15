import MainLayout from "../components/layout/MainLayout";
import ExperimentList from "../components/experiments/ExperimentList";
import useNovaSystem from "../hooks/useNovaSystem";

export default function Experiments(){

  useNovaSystem();

  return(

    <MainLayout>

      <h1>Experiments</h1>

      <ExperimentList />

    </MainLayout>

  )

}