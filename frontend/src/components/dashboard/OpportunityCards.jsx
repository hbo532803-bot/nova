export default function OpportunityCards({ opportunities = [] }) {

  if (!opportunities || opportunities.length === 0) {
    return (
      <div style={{padding:20}}>
        No opportunities available
      </div>
    );
  }

  return (

    <div style={{
      display:"grid",
      gridTemplateColumns:"repeat(auto-fill,minmax(250px,1fr))",
      gap:"20px",
      padding:"20px"
    }}>

      {opportunities.map((op,i)=>(
        <div
          key={i}
          style={{
            background:"#111827",
            padding:"20px",
            borderRadius:"10px"
          }}
        >

          <h3>{op.title || "Opportunity"}</h3>

          <p>{op.description || "No description"}</p>

        </div>
      ))}

    </div>
  );
}