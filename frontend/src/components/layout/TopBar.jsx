import { useNavigate } from "react-router-dom";

export default function TopBar({ onMenuToggle, showMenuButton = false }){

  const navigate = useNavigate();

  function logout(){
    localStorage.removeItem("nova_token");
    navigate("/login");
  }

  return(

    <div style={{
      height:"60px",
      background:"#020617",
      borderBottom:"1px solid #1e293b",
      display:"flex",
      alignItems:"center",
      justifyContent:"space-between",
      padding:"0 20px"
    }}>

      <span>NOVA CONTROL SYSTEM</span>

      <div style={{ display: "flex", gap: 8 }}>
        {showMenuButton ? (
          <button
            onClick={onMenuToggle}
            style={{
              background:"#1d4ed8",
              border:"none",
              padding:"6px 12px",
              color:"white",
              borderRadius:"6px",
              cursor:"pointer"
            }}
          >
            Menu
          </button>
        ) : null}
        <button
          onClick={logout}
          style={{
            background:"#dc2626",
            border:"none",
            padding:"6px 12px",
            color:"white",
            borderRadius:"6px",
            cursor:"pointer"
          }}
        >
          Logout
        </button>
      </div>

    </div>

  )
}
