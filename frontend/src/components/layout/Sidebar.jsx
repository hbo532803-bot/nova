import { NavLink } from "react-router-dom";

const linkStyle = {
  padding: "12px 16px",
  display: "block",
  textDecoration: "none",
  color: "#cbd5f5"
};

export default function Sidebar() {
  return (
    <div
      style={{
        width: "220px",
        background: "#020617",
        borderRight: "1px solid #1e293b"
      }}
    >
      <h2 style={{ padding: "20px" }}>NOVA ADMIN</h2>

      <nav>
        <NavLink to="/dashboard" style={linkStyle}>Dashboard</NavLink>
        <NavLink to="/agents" style={linkStyle}>Agents</NavLink>
        <NavLink to="/opportunities" style={linkStyle}>Opportunities</NavLink>
        <NavLink to="/execution" style={linkStyle}>Execution</NavLink>
        <NavLink to="/social" style={linkStyle}>Social Growth</NavLink>
        <NavLink to="/logs" style={linkStyle}>Logs</NavLink>
        <NavLink to="/experiments" style={linkStyle}>Experiments</NavLink>
      </nav>
    </div>
  );
}
