import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";

export default function Login() {
  const [pw, setPw] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const setToken = useAuth(s => s.setToken);
  const nav = useNavigate();
  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const r = await api.post("/api/login", { password: pw });
      setToken(r.data.token);
      nav("/runs");
    } catch { setErr("Invalid password"); }
  }
  return (
    <div className="max-w-sm mx-auto mt-24 p-6 border rounded space-y-3">
      <h1 className="text-xl font-bold">airedteam login</h1>
      <form onSubmit={submit} className="space-y-2">
        <input type="password" className="w-full border rounded px-2 py-1" placeholder="admin password" value={pw} onChange={e => setPw(e.target.value)} />
        <button className="px-3 py-1 bg-black text-white rounded" type="submit">Sign in</button>
      </form>
      {err && <div className="text-red-600 text-sm">{err}</div>}
    </div>
  );
}
