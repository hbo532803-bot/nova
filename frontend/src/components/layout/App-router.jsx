import { BrowserRouter, Routes, Route } from "react-router-dom";

import Login from "../../pages/login";
import Dashboard from "../../pages/dashboard";
import Agents from "../../pages/agents";
import Opportunities from "../../pages/opportunities";
import Execution from "../../pages/execution";
import Experiments from "../../pages/experiments";
import Logs from "../../pages/logs";

import ProtectedRoute from "../auth/ProtectedRoute";

export default function AppRouter() {
  return (
    <BrowserRouter>

      <Routes>

        <Route path="/login" element={<Login />} />

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/agents"
          element={
            <ProtectedRoute>
              <Agents />
            </ProtectedRoute>
          }
        />

        <Route
          path="/opportunities"
          element={
            <ProtectedRoute>
              <Opportunities />
            </ProtectedRoute>
          }
        />

        <Route
          path="/execution"
          element={
            <ProtectedRoute>
              <Execution />
            </ProtectedRoute>
          }
        />

        <Route
          path="/experiments"
          element={
            <ProtectedRoute>
              <Experiments />
            </ProtectedRoute>
          }
        />

        <Route
          path="/logs"
          element={
            <ProtectedRoute>
              <Logs />
            </ProtectedRoute>
          }
        />

        <Route path="/" element={<Login />} />

      </Routes>

    </BrowserRouter>
  );
}