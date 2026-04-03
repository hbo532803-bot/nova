import MainLayout from "../components/layout/MainLayout";
import { useNovaStore } from "../state/novaStore";
import useEventBus from "../hooks/useEventBus";
import useNovaSystem from "../hooks/useNovaSystem";

export default function Logs(){

  useNovaSystem();
  useEventBus();

  const logs = useNovaStore((s)=>s.logs);

  return(

    <MainLayout>

      <h1>Activity Logs</h1>

      {(logs || []).map((log,i)=>(

        <div
          key={i}
          style={{
            background:"#020617",
            padding:"10px",
            borderBottom:"1px solid #1e293b"
          }}
        >

          {log.message || JSON.stringify(log)}

        </div>

      ))}

    </MainLayout>

  )
}