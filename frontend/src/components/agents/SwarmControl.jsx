import { useNovaStore } from "../../state/novaStore";
import { hibernateAgent, wakeAgent } from "../../services/consoleApi";

export default function SwarmControl(){

  const agents = useNovaStore(s=>s.agents) || [];

  async function wakeAll(){

    for(const agent of agents){

      try{

        await wakeAgent(agent.id);

      }
      catch(e){

        console.error("Agent wake failed",agent.id);

      }

    }

    alert("Wake queued for all agents");

  }

  async function hibernateAll(){
    for(const agent of agents){
      try{
        await hibernateAgent(agent.id);
      }catch(e){
        console.error("Agent hibernate failed",agent.id);
      }
    }
    alert("Hibernate queued for all agents");
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

      <div style={{display:"flex",gap:"10px",flexWrap:"wrap"}}>
        <button
          onClick={wakeAll}
          style={{
            padding:"8px 14px",
            background:"#16a34a",
            border:"none",
            color:"white",
            borderRadius:"6px",
            cursor:"pointer"
          }}
        >
          Wake all
        </button>

        <button
          onClick={hibernateAll}
          style={{
            padding:"8px 14px",
            background:"#dc2626",
            border:"none",
            color:"white",
            borderRadius:"6px",
            cursor:"pointer"
          }}
        >
          Hibernate all
        </button>
      </div>

    </div>

  )

}