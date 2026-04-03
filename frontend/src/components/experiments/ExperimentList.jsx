import { useNovaStore } from "../../state/novaStore";
import { runExperimentById } from "../../services/consoleApi";

export default function ExperimentList(){

  const experiments = useNovaStore(s=>s.experiments) || [];

  async function startExperiment(id){

    try{

      await runExperimentById(id);

      alert("Experiment started");

    }
    catch(e){

      console.error(e);
      alert("Experiment failed");

    }

  }

  if(experiments.length===0){

    return(
      <div style={{padding:"20px"}}>
        No experiments available
      </div>
    );

  }

  return(

    <div style={{
      display:"grid",
      gridTemplateColumns:"repeat(auto-fill,minmax(300px,1fr))",
      gap:"20px"
    }}>

      {experiments.map((exp,i)=>(

        <div
          key={i}
          style={{
            background:"#020617",
            padding:"20px",
            border:"1px solid #1e293b",
            borderRadius:"10px"
          }}
        >

          <h3>{exp.name || "Experiment"}</h3>

          <p>Status: {exp.status || "idle"}</p>

          <button
            onClick={()=>startExperiment(exp.id)}
            style={{
              marginTop:"10px",
              padding:"8px 14px",
              background:"#2563eb",
              border:"none",
              color:"white",
              borderRadius:"6px",
              cursor:"pointer"
            }}
          >

            Run Experiment

          </button>

        </div>

      ))}

    </div>

  )

}