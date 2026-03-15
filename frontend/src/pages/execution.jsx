import MainLayout from "../components/layout/MainLayout";
import { useNovaStore } from "../state/novaStore";

export default function Execution(){

  const execution = useNovaStore((s)=>s.execution);

  return(

    <MainLayout>

      <h1>Execution Pipeline</h1>

      <table style={{width:"100%",borderCollapse:"collapse"}}>

        <thead>
          <tr>
            <th>Task</th>
            <th>Status</th>
          </tr>
        </thead>

        <tbody>

        {(execution || []).map((task,i)=>(
          <tr key={i}>

            <td>{task.name || "Task"}</td>
            <td>{task.status || "pending"}</td>

          </tr>
        ))}

        </tbody>

      </table>

    </MainLayout>

  )
}