import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import { useAuth } from "./lib/auth";

const Login = lazy(() => import("./pages/Login"));
const Dashboard = lazy(() => import("./pages/Dashboard"));
const Targets = lazy(() => import("./pages/Targets"));
const Reconnaissance = lazy(() => import("./pages/Reconnaissance"));
const Assets = lazy(() => import("./pages/Assets"));
const AttackMethods = lazy(() => import("./pages/AttackMethods"));
const Runs = lazy(() => import("./pages/Runs"));
const RunDetail = lazy(() => import("./pages/RunDetail"));
const NewRun = lazy(() => import("./pages/NewRun"));
const RetestRun = lazy(() => import("./pages/RetestRun"));
const ManualConsole = lazy(() => import("./pages/ManualConsole"));
const Settings = lazy(() => import("./pages/Settings"));

function Protected({ children }: { children: JSX.Element }) {
  const t = useAuth(s => s.token);
  return t ? children : <Navigate to="/login" replace />;
}

function PageFallback() {
  return (
    <div className="min-h-screen bg-gray-50 p-6" aria-busy="true" aria-label="Loading">
      <div className="mx-auto max-w-7xl animate-pulse space-y-6">
        <div className="h-8 w-52 rounded bg-gray-200" />
        <div className="grid gap-4 md:grid-cols-4">
          {[0, 1, 2, 3].map(item => <div key={item} className="h-28 rounded-xl bg-white shadow-sm" />)}
        </div>
        <div className="h-72 rounded-xl bg-white shadow-sm" />
      </div>
    </div>
  );
}

export default function App() {
  return (
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<Protected><Layout /></Protected>}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/targets" element={<Targets />} />
          <Route path="/reconnaissance" element={<Reconnaissance />} />
          <Route path="/assets" element={<Assets />} />
          <Route path="/attack-methods" element={<AttackMethods />} />
          <Route path="/datasets" element={<Navigate to="/assets" replace />} />
          <Route path="/runs" element={<Runs />} />
          <Route path="/runs/new" element={<NewRun />} />
          <Route path="/runs/retest" element={<RetestRun />} />
          <Route path="/runs/:id" element={<RunDetail />} />
          <Route path="/manual" element={<ManualConsole />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/prompt-assets" element={<Navigate to="/assets?tab=prompt-templates" replace />} />
        </Route>
      </Routes>
    </Suspense>
  );
}
