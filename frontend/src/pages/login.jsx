import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../services/apiConfig";

const API = API_BASE_URL;

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const navigate = useNavigate();

  async function login() {
    setError("");
    if (!username.trim() || !password.trim()) {
      setError("Username and password are required.");
      return;
    }

    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      setLoading(true);
      const res = await fetch(`${API}/api/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: formData,
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data.access_token) {
        setError(data.detail || "Login failed");
        return;
      }

      localStorage.setItem("nova_token", data.access_token);
      navigate("/dashboard");
    } catch {
      setError("Unable to connect to Nova backend.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 40 }}>
      <h1>NOVA LOGIN</h1>

      <input placeholder="username" onChange={(e) => setUsername(e.target.value)} />

      <br />
      <br />

      <input
        type="password"
        placeholder="password"
        onChange={(e) => setPassword(e.target.value)}
      />

      <br />
      <br />

      <button onClick={login} disabled={loading}>
        {loading ? "Signing in..." : "Login"}
      </button>
      {error && <p style={{ color: "#ef4444", marginTop: 12 }}>{error}</p>}
    </div>
  );
}
