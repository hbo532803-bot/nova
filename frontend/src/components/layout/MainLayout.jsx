import { useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function MainLayout({ children }) {
  const [isMobile, setIsMobile] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onResize = () => {
      const mobile = window.innerWidth < 900;
      setIsMobile(mobile);
      if (!mobile) setMenuOpen(false);
    };
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  return (
    <div style={{display:"flex",height:"100vh",background:"#0b1220",color:"white"}}>

      <Sidebar
        isMobile={isMobile}
        isOpen={!isMobile || menuOpen}
        onNavigate={() => {
          if (isMobile) setMenuOpen(false);
        }}
      />

      <div style={{flex:1,display:"flex",flexDirection:"column"}}>

        <TopBar showMenuButton={isMobile} onMenuToggle={() => setMenuOpen((v) => !v)} />

        <main style={{flex:1,overflow:"auto",padding:"20px"}}>
          {children}
        </main>

      </div>

    </div>
  );
}
