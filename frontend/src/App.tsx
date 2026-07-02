import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import { useAuth } from "./lib/auth";

const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Targets = lazy(() => import("./pages/Targets"));
const Assets = lazy(() => import("./pages/Assets"));
const AttackMethods = lazy(() => import("./pages/AttackMethods"));
const Runs = lazy(() => import("./pages/Runs"));
const RunDetail = lazy(() => import("./pages/RunDetail"));
const NewRun = lazy(() => import("./pages/NewRun"));
const ManualConsole = lazy(() => import("./pages/ManualConsole"));
const Settings = lazy(() => import("./pages/Settings"));

function Protected({ children }: { children: JSX.Element }) {
  const t = useAuth(s => s.token);
  return t ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Suspense fallback={null}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<Protected><Layout /></Protected>}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/assets" element={<Assets />} />
          <Route path="/attack-methods" element={<AttackMethods />} />
          <Route path="/datasets" element={<Navigate to="/assets" replace />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/runs/new" element={<NewRun />} />
          <Route path="/runs/:id" element={<RunDetail />} />
          <Route path="/manual" element={<ManualConsole />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/prompt-assets" element={<Navigate to="/assets?tab=prompt-templates" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
