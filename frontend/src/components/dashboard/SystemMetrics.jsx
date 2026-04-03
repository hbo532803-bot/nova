import { useNovaStore } from "../../state/novaStore";

export default function SystemMetrics(){

  const systemState = useNovaStore(s=>s.systemState);
  const confidence = useNovaStore(s=>s.confidence);

  const state = systemState?.state ?? "UNKNOWN";
  const score = confidence?.score ?? "-";
  const autonomy = confidence?.autonomy ?? "-";

  return(

    <div style={{
      display:"grid",
      gridTemplateColumns:"repeat(3,1fr)",
      gap:"20px",
      marginBottom:"20px"
    }}>

      <Metric title="System State" value={state} />

      <Metric title="Confidence" value={score} />

      <Metric title="Autonomy" value={autonomy} />

    </div>

  )
}

function Metric({title,value}){

  return(

    <div style={{
      background:"#020617",
      padding:"20px",
      borderRadius:"10px",
      border:"1px solid #1e293b"
    }}>

      <p style={{opacity:.7}}>{title}</p>

      <h2>{value}</h2>

    </div>

  )

}