import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";

export default function Layout() {
  const setToken = useAuth(s => s.setToken);
  const nav = useNavigate();
  const link = "px-3 py-1 rounded hover:bg-gray-200";
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b p-3 flex gap-2 items-center">
        <span className="font-bold mr-4">airedteam</span>
        <NavLink to="/targets" className={link}>Targets</NavLink>
        <NavLink to="/datasets" className={link}>Datasets</NavLink>
        <NavLink to="/runs" className={link}>Runs</NavLink>
        <NavLink to="/runs/new" className={link}>New run</NavLink>
        <div className="ml-auto">
          <button className={link} onClick={() => { setToken(null); nav("/login"); }}>Logout</button>
        </div>
      </header>
      <main className="flex-1 p-4"><Outlet /></main>
    </div>
  );
}
