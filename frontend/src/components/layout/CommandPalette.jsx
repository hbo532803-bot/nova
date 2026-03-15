import { useState } from "react";

export default function CommandPalette({ commands }) {
  const [query, setQuery] = useState("");

  const filtered = commands.filter((c) =>
    c.toLowerCase().includes(query.toLowerCase())
  );

  return (
    <div
      style={{
        background: "#111827",
        padding: "20px",
        borderRadius: "8px",
        width: "400px"
      }}
    >
      <input
        type="text"
        placeholder="Command..."
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{
          width: "100%",
          padding: "10px",
          marginBottom: "10px",
          background: "#1f2937",
          border: "none",
          color: "white"
        }}
      />

      {filtered.map((cmd, i) => (
        <div
          key={i}
          style={{
            padding: "8px",
            borderBottom: "1px solid #374151"
          }}
        >
          {cmd}
        </div>
      ))}
    </div>
  );
}