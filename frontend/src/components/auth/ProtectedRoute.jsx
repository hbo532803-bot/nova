import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";
import { validateStoredSession } from "../../services/auth";

export default function ProtectedRoute({children}){
  const [checking, setChecking] = useState(true);
  const [valid, setValid] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      const res = await validateStoredSession();
      if (!active) return;
      setValid(Boolean(res.valid));
      setChecking(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  if (checking) {
    return <div style={{ padding: 24 }}>Validating session…</div>;
  }

  if(!valid){
    return <Navigate to="/login" replace />
  }

  return children;
}
