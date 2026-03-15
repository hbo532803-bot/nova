import MainLayout from "../components/layout/MainLayout";
import { useNovaStore } from "../state/novaStore";

export default function Agents(){

  const agents = useNovaStore((s)=>s.agents);

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

          </div>
        ))}

      </div>

    </MainLayout>

  )
}