import { useNovaStore } from "../../state/novaStore";

export default function SystemMetrics(){

  const system = useNovaStore(s=>s.system);

  const cpu = system?.cpu ?? 0;
  const memory = system?.memory ?? 0;
  const tasks = system?.tasks ?? 0;

  return(

    <div style={{
      display:"grid",
      gridTemplateColumns:"repeat(3,1fr)",
      gap:"20px",
      marginBottom:"20px"
    }}>

      <Metric title="CPU Usage" value={`${cpu}%`} />

      <Metric title="Memory Usage" value={`${memory}%`} />

      <Metric title="Active Tasks" value={tasks} />

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