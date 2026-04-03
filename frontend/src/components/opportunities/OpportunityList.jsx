import { useNovaStore } from "../../state/novaStore";
import { approveOpportunity, rejectOpportunity, convertOpportunity } from "../../services/consoleApi";

export default function OpportunityList(){

  const opportunities = useNovaStore(s=>s.opportunities) || [];

  async function approve(id){

    try{

      await approveOpportunity(id);

      alert("Approved (queued)");

    }
    catch(e){

      console.error(e);
      alert("Action failed");

    }

  }

  async function reject(id){
    try{
      await rejectOpportunity(id);
      alert("Rejected (queued)");
    }catch(e){
      console.error(e);
      alert("Action failed");
    }
  }

  async function convert(id){
    try{
      await convertOpportunity(id);
      alert("Convert to experiment queued");
    }catch(e){
      console.error(e);
      alert("Action failed");
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

          <h3>{op.niche_name || op.title || "Opportunity"}</h3>

          <p style={{opacity:.8}}>Cash score: {op.cash_score}</p>
          <p style={{opacity:.8}}>Budget: {op.proposed_budget}</p>
          <p>Status: {op.status}</p>

          <div style={{display:"flex",gap:"10px",marginTop:"10px",flexWrap:"wrap"}}>
            <button
              onClick={()=>approve(op.id)}
              style={{
                padding:"8px 14px",
                background:"#16a34a",
                border:"none",
                color:"white",
                borderRadius:"6px",
                cursor:"pointer"
              }}
            >
              Approve
            </button>
            <button
              onClick={()=>reject(op.id)}
              style={{
                padding:"8px 14px",
                background:"#dc2626",
                border:"none",
                color:"white",
                borderRadius:"6px",
                cursor:"pointer"
              }}
            >
              Reject
            </button>
            <button
              onClick={()=>convert(op.id)}
              style={{
                padding:"8px 14px",
                background:"#2563eb",
                border:"none",
                color:"white",
                borderRadius:"6px",
                cursor:"pointer"
              }}
            >
              Convert → Experiment
            </button>
          </div>

        </div>

      ))}

    </div>

  )

}