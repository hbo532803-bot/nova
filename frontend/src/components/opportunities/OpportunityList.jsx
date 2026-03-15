import { runOpportunity } from "../../services/novaApi";
import { useNovaStore } from "../../state/novaStore";

export default function OpportunityList(){

  const opportunities = useNovaStore(s=>s.opportunities) || [];

  async function executeOpportunity(id){

    try{

      await runOpportunity(id);

      alert("Opportunity execution started");

    }
    catch(e){

      console.error(e);
      alert("Execution failed");

    }

  }

  if(opportunities.length===0){

    return(
      <div style={{padding:"20px"}}>
        No opportunities discovered
      </div>
    );

  }

  return(

    <div style={{
      display:"grid",
      gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))",
      gap:"20px"
    }}>

      {opportunities.map((op,i)=>(

        <div
          key={i}
          style={{
            background:"#020617",
            padding:"20px",
            border:"1px solid #1e293b",
            borderRadius:"10px"
          }}
        >

          <h3>{op.title || "Opportunity"}</h3>

          <p>{op.description || "No description"}</p>

          <button
            onClick={()=>executeOpportunity(op.id)}
            style={{
              marginTop:"10px",
              padding:"8px 14px",
              background:"#16a34a",
              border:"none",
              color:"white",
              borderRadius:"6px",
              cursor:"pointer"
            }}
          >

            Execute

          </button>

        </div>

      ))}

    </div>

  )

}