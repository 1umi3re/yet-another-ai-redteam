import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

type T = { id: string; name: string; plugin: string; params: Record<string, any>; has_secret: boolean };

export default function Targets() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["targets"], queryFn: async () => (await api.get<T[]>("/api/targets")).data });
  const [form, setForm] = useState({ name: "", plugin: "openai_compat", base_url: "", model: "", api_key: "" });
  const create = useMutation({
    mutationFn: async () => api.post("/api/targets", {
      name: form.name,
      plugin: form.plugin,
      params: { name: form.name, base_url: form.base_url, model: form.model },
      secret: { api_key: form.api_key },
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["targets"] }),
  });
  const del = useMutation({
    mutationFn: async (id: string) => api.delete(`/api/targets/${id}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["targets"] }),
  });
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Targets</h1>
      <div className="p-4 border rounded space-y-2 max-w-xl">
        <h2 className="font-semibold">New target</h2>
        {(["name","base_url","model","api_key"] as const).map(k => (
          <input key={k} placeholder={k} className="w-full border rounded px-2 py-1"
                 value={(form as any)[k]} onChange={e => setForm({ ...form, [k]: e.target.value })} />
        ))}
        <select className="border rounded px-2 py-1" value={form.plugin} onChange={e => setForm({ ...form, plugin: e.target.value })}>
          <option value="openai_compat">openai_compat</option>
          <option value="anthropic_compat">anthropic_compat</option>
        </select>
        <button className="px-3 py-1 bg-black text-white rounded" onClick={() => create.mutate()}>Create</button>
      </div>
      <table className="w-full border-collapse">
        <thead><tr className="text-left border-b"><th>Name</th><th>Plugin</th><th>Model</th><th></th></tr></thead>
        <tbody>{data?.map(t => (
          <tr key={t.id} className="border-b">
            <td>{t.name}</td><td>{t.plugin}</td><td>{t.params?.model}</td>
            <td><button className="text-red-600" onClick={() => del.mutate(t.id)}>Delete</button></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}
