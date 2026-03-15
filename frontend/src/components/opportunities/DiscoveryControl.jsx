import { discoverOpportunities } from "../../services/novaApi";

export default function DiscoveryControl(){

  async function scan(){

    try{

      await discoverOpportunities();

      alert("Opportunity scan started");

    }
    catch(e){

      console.error(e);
      alert("Scan failed");

    }

  }

  return(

    <div style={{
      background:"#020617",
      padding:"20px",
      border:"1px solid #1e293b",
      borderRadius:"10px",
      marginBottom:"20px"
    }}>

      <h3>Opportunity Discovery</h3>

      <p>Scan external data sources for new opportunities.</p>

      <button
        onClick={scan}
        style={{
          padding:"8px 14px",
          background:"#9333ea",
          border:"none",
          color:"white",
          borderRadius:"6px"
        }}
      >
        Scan Opportunities
      </button>

    </div>

  )

}