import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "../lib/api";

export default function Runs() {
  const { data } = useQuery({
    queryKey: ["runs"],
    queryFn: async () => (await api.get("/api/runs")).data,
    refetchInterval: 2000,
  });
  return (
    <div>
      <h1 className="text-xl font-bold mb-3">Runs</h1>
      <table className="w-full">
        <thead><tr className="text-left border-b"><th>Name</th><th>Status</th><th>Progress</th><th></th></tr></thead>
        <tbody>{data?.map((r: any) => (
          <tr key={r.id} className="border-b">
            <td>{r.name}</td><td>{r.status}</td><td>{r.progress_done}/{r.progress_total}</td>
            <td><Link className="text-blue-600" to={`/runs/${r.id}`}>open</Link></td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}
