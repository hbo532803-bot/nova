import { restartAgent } from "../../services/novaApi";

export default function AgentList({agents=[]}){

  async function restart(id){

    try{

      await restartAgent(id);

      alert("Agent restarted");

    }
    catch(e){

      alert("Restart failed");

    }

  }

  return(

    <div style={{
      display:"grid",
      gridTemplateColumns:"repeat(auto-fill,minmax(250px,1fr))",
      gap:"20px"
    }}>

      {agents.map((agent,i)=>(

        <div
          key={i}
          style={{
            background:"#020617",
            padding:"20px",
            border:"1px solid #1e293b",
            borderRadius:"10px"
          }}
        >

          <h3>{agent.name || "Agent"}</h3>

          <p>Status: {agent.status || "idle"}</p>

          <button
            onClick={()=>restart(agent.id)}
            style={{
              marginTop:"10px",
              padding:"6px 10px",
              background:"#2563eb",
              border:"none",
              color:"white",
              borderRadius:"6px"
            }}
          >
            Restart
          </button>

        </div>

      ))}

    </div>

  )
}