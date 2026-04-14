import { NavLink } from "react-router-dom";

const linkStyle = {
  padding: "12px 16px",
  display: "block",
  textDecoration: "none",
  color: "#cbd5f5"
};

export default function Sidebar({ isMobile = false, isOpen = true, onNavigate = () => {} }) {
  if (!isOpen) return null;
  return (
    <div
      style={{
        position: isMobile ? "fixed" : "relative",
        zIndex: 20,
        top: isMobile ? 60 : "auto",
        left: 0,
        bottom: isMobile ? 0 : "auto",
        width: "220px",
        minWidth: "220px",
        height: isMobile ? "calc(100vh - 60px)" : "auto",
        background: "#020617",
        borderRight: "1px solid #1e293b",
        boxShadow: isMobile ? "8px 0 20px rgba(0,0,0,0.35)" : "none"
      }}
    >
      <h2 style={{ padding: "20px" }}>NOVA ADMIN</h2>

      <nav>
        <NavLink to="/dashboard" style={linkStyle} onClick={onNavigate}>Dashboard</NavLink>
        <NavLink to="/agents" style={linkStyle} onClick={onNavigate}>Agents</NavLink>
        <NavLink to="/opportunities" style={linkStyle} onClick={onNavigate}>Opportunities</NavLink>
        <NavLink to="/execution" style={linkStyle} onClick={onNavigate}>Execution</NavLink>
        <NavLink to="/social" style={linkStyle} onClick={onNavigate}>Social Growth</NavLink>
        <NavLink to="/logs" style={linkStyle} onClick={onNavigate}>Logs</NavLink>
        <NavLink to="/experiments" style={linkStyle} onClick={onNavigate}>Experiments</NavLink>
      </nav>
    </div>
  );
}
