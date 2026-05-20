import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api } from "../lib/api";
import { Card, CardBody, CardHeader, CardTitle, CardDescription } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input, Field } from "../components/ui/Form";
import { Badge } from "../components/ui/Badge";
import { EmptyState } from "../components/ui/EmptyState";
import { Database, Upload } from "lucide-react";
import { toast } from "sonner";
import { useI18n } from "../lib/i18n";

type D = { id: string; name: string; plugin: string; item_count: number | null };

export default function Datasets() {
  const { t } = useI18n();
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({
    queryKey: ["datasets"],
    queryFn: async () => (await api.get<D[]>("/api/datasets")).data,
  });
  const [name, setName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const upload = useMutation({
    mutationFn: async () => {
      const fd = new FormData(); fd.append("name", name);
      if (file) fd.append("file", file);
      return api.post("/api/datasets/upload", fd, { headers: { "Content-Type": "multipart/form-data" } });
    },
    onSuccess: () => {
      toast.success(t("Dataset uploaded"));
      setName(""); setFile(null);
      qc.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? t("Upload failed")),
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("Datasets")}</h1>
        <p className="text-sm text-gray-500 mt-1">{t("Prompt collections used as the source material for attacks.")}</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("Upload JSON dataset")}</CardTitle>
          <CardDescription>
            {t("JSON file with an array of items. Each item should have a")} <code className="font-mono text-xs bg-gray-100 px-1 rounded">prompt</code> {t("field.")}
          </CardDescription>
        </CardHeader>
        <CardBody>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Field label={t("Dataset name")}><Input placeholder={t("e.g. my-jailbreaks")} value={name} onChange={e => setName(e.target.value)} /></Field>
            <Field label={t("JSON file")}>
              <label className="flex items-center justify-center gap-2 border-2 border-dashed border-gray-200 rounded-lg px-3 py-3 text-sm cursor-pointer hover:border-brand-400 hover:bg-brand-50/40 transition">
                <Upload className="h-4 w-4 text-gray-400" />
                <span className="text-gray-600">{file ? file.name : t("Choose JSON file…")}</span>
                <input type="file" accept=".json,application/json" className="hidden"
                  onChange={e => setFile(e.target.files?.[0] ?? null)} />
              </label>
            </Field>
          </div>
          <div className="mt-5 flex justify-end">
            <Button icon={<Upload className="h-4 w-4" />} loading={upload.isPending}
              disabled={!name || !file} onClick={() => upload.mutate()}>{t("Upload")}</Button>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>{t("Available datasets")}</CardTitle>
          <CardDescription>{t("Built-in AdvBench/HarmBench samples appear here after running")} <code className="font-mono text-xs bg-gray-100 px-1 rounded">airedteam seed-datasets</code>.</CardDescription>
        </CardHeader>
        {isLoading ? (
          <CardBody className="text-sm text-gray-500">{t("Loading…")}</CardBody>
        ) : !data?.length ? (
          <EmptyState icon={<Database className="h-10 w-10" />} title={t("No datasets yet")}
            description={t("Upload a JSON file or seed the built-in samples.")} />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left px-5 py-2.5">{t("Name")}</th>
                  <th className="text-left px-5 py-2.5">{t("Plugin")}</th>
                  <th className="text-left px-5 py-2.5">{t("Items")}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {data.map(d => (
                  <tr key={d.id}>
                    <td className="px-5 py-3 font-medium">{d.name}</td>
                    <td className="px-5 py-3"><Badge tone="indigo">{d.plugin}</Badge></td>
                    <td className="px-5 py-3 tabular-nums text-gray-700">{d.item_count ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}
