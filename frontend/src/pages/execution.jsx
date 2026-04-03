import MainLayout from "../components/layout/MainLayout";
import { useNovaStore } from "../state/novaStore";
import useNovaSystem from "../hooks/useNovaSystem";

export default function Execution(){

  useNovaSystem();
  const commands = useNovaStore((s)=>s.commands) || [];

  return(

    <MainLayout>

      <h1>Command History</h1>

      <table style={{width:"100%",borderCollapse:"collapse"}}>

        <thead>
          <tr>
            <th>ID</th>
            <th>Command</th>
            <th>Status</th>
            <th>Created</th>
          </tr>
        </thead>

        <tbody>

        {commands.map((c,i)=>(
          <tr key={c.id ?? i}>

            <td>{c.id}</td>
            <td>{c.command_text}</td>
            <td>{c.status}</td>
            <td>{c.created_at}</td>

          </tr>
        ))}

        </tbody>

      </table>

    </MainLayout>

  )
}