import { restartAgent } from "../../services/novaApi";
import { useNovaStore } from "../../state/novaStore";

export default function SwarmControl(){

  const agents = useNovaStore(s=>s.agents) || [];

  async function restartAll(){

    for(const agent of agents){

      try{

        await restartAgent(agent.id);

      }
      catch(e){

        console.error("Agent restart failed",agent.id);

      }

    }

    alert("Swarm restart triggered");

  }

  return(

    <div style={{
      background:"#020617",
      padding:"20px",
      borderRadius:"10px",
      border:"1px solid #1e293b",
      marginBottom:"20px"
    }}>

      <h3>Agent Swarm</h3>

      <p>Total Agents: {agents.length}</p>

      <button
        onClick={restartAll}
        style={{
          padding:"8px 14px",
          background:"#2563eb",
          border:"none",
          color:"white",
          borderRadius:"6px"
        }}
      >

        Restart Swarm

      </button>

    </div>

  )

}