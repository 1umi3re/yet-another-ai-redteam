import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";

type D = { id: string; name: string; plugin: string; item_count: number | null };

export default function Datasets() {
  const qc = useQueryClient();
  const { data } = useQuery({ queryKey: ["datasets"], queryFn: async () => (await api.get<D[]>("/api/datasets")).data });
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const upload = useMutation({
    mutationFn: async () => {
      const fd = new FormData(); fd.append("name", name); if (file) fd.append("file", file);
      return api.post("/api/datasets/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["datasets"] }),
  });
  return (
    <div className="space-y-6">
      <h1 className="text-xl font-bold">Datasets</h1>
      <div className="p-4 border rounded max-w-xl space-y-2">
        <input placeholder="name" className="w-full border rounded px-2 py-1" value={name} onChange={e => setName(e.target.value)} />
        <input type="file" accept=".json,application/json" onChange={e => setFile(e.target.files?.[0] ?? null)} />
        <button className="px-3 py-1 bg-black text-white rounded" onClick={() => upload.mutate()}>Upload JSON</button>
      </div>
      <table className="w-full">
        <thead><tr className="text-left border-b"><th>Name</th><th>Plugin</th><th>Items</th></tr></thead>
        <tbody>{data?.map(d => (
          <tr key={d.id} className="border-b"><td>{d.name}</td><td>{d.plugin}</td><td>{d.item_count ?? "-"}</td></tr>
        ))}</tbody>
      </table>
    </div>
  );
}
