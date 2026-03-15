import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function MainLayout({ children }) {

  return (
    <div style={{display:"flex",height:"100vh",background:"#0b1220",color:"white"}}>

      <Sidebar />

      <div style={{flex:1,display:"flex",flexDirection:"column"}}>

        <TopBar />

        <main style={{flex:1,overflow:"auto",padding:"20px"}}>
          {children}
        </main>

      </div>

    </div>
  );
}