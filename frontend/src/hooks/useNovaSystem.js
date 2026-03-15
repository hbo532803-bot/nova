import { useEffect } from "react";
import { useNovaStore } from "../state/novaStore";
import {
  fetchDashboard,
  fetchAgents,
  fetchOpportunities,
  fetchExecution,
  fetchLogs
} from "../services/novaApi";

export default function useNovaSystem(){

  const setSystem = useNovaStore(s=>s.setSystem);
  const setAgents = useNovaStore(s=>s.setAgents);
  const setOpportunities = useNovaStore(s=>s.setOpportunities);
  const setExecution = useNovaStore(s=>s.setExecution);
  const setLogs = useNovaStore(s=>s.setLogs);

  useEffect(()=>{

    async function load(){

      try{

        const dash = await fetchDashboard();
        const agents = await fetchAgents();
        const opp = await fetchOpportunities();
        const exec = await fetchExecution();
        const logs = await fetchLogs();

        setSystem(dash?.system||{});
        setAgents(agents||[]);
        setOpportunities(opp||[]);
        setExecution(exec||[]);
        setLogs(logs||[]);

      }
      catch(e){

        console.error("Nova load failed",e);

      }

    }

    load();

    const timer = setInterval(load,5000);

    return ()=>clearInterval(timer);

  },[]);
}