export default function MetricsPanel({ metrics }) {

  if(!metrics){
    return <div style={{padding:20}}>Metrics loading...</div>;
  }

  return(

    <div style={{padding:20}}>

      <h2>Metrics</h2>

      <p>CPU: {metrics.cpu ?? 0}%</p>
      <p>Memory: {metrics.memory ?? 0}%</p>
      <p>Tasks/sec: {metrics.tps ?? 0}</p>

    </div>

  );
}