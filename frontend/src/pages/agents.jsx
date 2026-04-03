import MainLayout from "../components/layout/MainLayout";
import { useNovaStore } from "../state/novaStore";
import useNovaSystem from "../hooks/useNovaSystem";
import { hibernateAgent, wakeAgent } from "../services/consoleApi";

export default function Agents(){

  useNovaSystem();

  const agents = useNovaStore((s)=>s.agents);

  async function setState(agent, target){
    try{
      if(target==="HIBERNATED"){
        await hibernateAgent(agent.id);
        alert("Hibernate queued");
      }else{
        await wakeAgent(agent.id);
        alert("Wake queued");
      }
    }catch(e){
      console.error(e);
      alert("Action failed");
    }
  }

  return(

    <MainLayout>

      <h1>Agents</h1>

      <div style={{
        display:"grid",
        gridTemplateColumns:"repeat(auto-fill,minmax(250px,1fr))",
        gap:"20px"
      }}>

        {(agents || []).map((agent,i)=>(
          <div
            key={i}
            style={{
              background:"#020617",
              padding:"20px",
              borderRadius:"10px",
              border:"1px solid #1e293b"
            }}
          >

            <h3>{agent.name || "Agent"}</h3>

            <p>Status: {agent.status || "idle"}</p>

            <div style={{display:"flex",gap:"10px",marginTop:"12px"}}>
              <button
                onClick={()=>setState(agent,"HIBERNATED")}
                style={{
                  padding:"8px 12px",
                  background:"#dc2626",
                  border:"none",
                  color:"white",
                  borderRadius:"6px",
                  cursor:"pointer"
                }}
              >
                Hibernate
              </button>
              <button
                onClick={()=>setState(agent,"ACTIVE")}
                style={{
                  padding:"8px 12px",
                  background:"#16a34a",
                  border:"none",
                  color:"white",
                  borderRadius:"6px",
                  cursor:"pointer"
                }}
              >
                Wake
              </button>
            </div>

          </div>
        ))}

      </div>

    </MainLayout>

  )
}