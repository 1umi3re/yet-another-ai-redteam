import { Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Targets from "./pages/Targets";
import Datasets from "./pages/Datasets";
import Runs from "./pages/Runs";
import RunDetail from "./pages/RunDetail";
import NewRun from "./pages/NewRun";
import Layout from "./components/Layout";
import { useAuth } from "./lib/auth";

function Protected({ children }: { children: JSX.Element }) {
  const t = useAuth(s => s.token);
  return t ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route element={<Protected><Layout /></Protected>}>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/targets" element={<Targets />} />
        <Route path="/datasets" element={<Datasets />} />
        <Route path="/runs" element={<Runs />} />
        <Route path="/runs/new" element={<NewRun />} />
        <Route path="/runs/:id" element={<RunDetail />} />
      </Route>
    </Routes>
  );
}
