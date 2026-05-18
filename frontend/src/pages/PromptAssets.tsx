import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle, FileText, Plus, RotateCcw, Save } from "lucide-react";
import clsx from "clsx";
import { toast } from "sonner";

import { api } from "../lib/api";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "../components/ui/Card";
import { Field, Input, Textarea } from "../components/ui/Form";

type Override = {
  id: string;
  asset_id: string;
  name: string;
  template: string;
  is_active: boolean;
};

type Asset = {
  id: string;
  version: number;
  plugin: string;
  purpose: string;
  variables: string[];
  template: string;
  active_override?: Override | null;
  overrides?: Override[];
};

export default function PromptAssets() {
  const qc = useQueryClient();
  const { data: assets = [] } = useQuery<Asset[]>({
    queryKey: ["prompt-assets"],
    queryFn: async () => (await api.get("/api/prompt-assets")).data,
  });
  const [selectedId, setSelectedId] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [template, setTemplate] = useState("");

  useEffect(() => {
    if (!selectedId && assets.length > 0) setSelectedId(assets[0].id);
  }, [assets, selectedId]);

  const { data: asset } = useQuery<Asset>({
    queryKey: ["prompt-asset", selectedId],
    enabled: !!selectedId,
    queryFn: async () => (await api.get(`/api/prompt-assets/${selectedId}`)).data,
  });

  const selectedOverride = useMemo(
    () => asset?.overrides?.find(o => o.id === editingId) ?? null,
    [asset, editingId],
  );

  useEffect(() => {
    if (selectedOverride) {
      setName(selectedOverride.name);
      setTemplate(selectedOverride.template);
    }
  }, [selectedOverride]);

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["prompt-assets"] });
    qc.invalidateQueries({ queryKey: ["prompt-asset", selectedId] });
  };

  const saveMut = useMutation({
    mutationFn: async () => {
      if (!asset) return null;
      if (editingId) {
        return (await api.patch(`/api/prompt-assets/overrides/${editingId}`, { name, template })).data;
      }
      return (await api.post(`/api/prompt-assets/${asset.id}/overrides`, { name, template })).data;
    },
    onSuccess: (data) => {
      if (data?.id) setEditingId(data.id);
      refresh();
      toast.success("Prompt override saved");
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail ?? "Failed to save override"),
  });

  const activeMut = useMutation({
    mutationFn: async (override_id: string | null) =>
      (await api.post(`/api/prompt-assets/${asset?.id}/active`, { override_id })).data,
    onSuccess: () => {
      refresh();
      toast.success("Active prompt updated");
    },
    onError: () => toast.error("Failed to update active prompt"),
  });

  const startNew = () => {
    setEditingId(null);
    setName(`${asset?.plugin ?? "Prompt"} override`);
    setTemplate(asset?.template ?? "");
  };

  useEffect(() => {
    if (asset) startNew();
  }, [asset?.id]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          <FileText className="h-6 w-6" />
          Prompt Assets
        </h1>
        <p className="text-sm text-gray-600 mt-1">Manage evaluator and executor prompt overrides.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[340px_minmax(0,1fr)] gap-4">
        <Card>
          <CardHeader><CardTitle>Assets</CardTitle></CardHeader>
          <CardBody className="space-y-2">
            {assets.map(a => (
              <button key={a.id} type="button" onClick={() => setSelectedId(a.id)}
                className={clsx(
                  "w-full rounded-lg border px-3 py-2 text-left transition",
                  selectedId === a.id ? "border-brand-500 bg-brand-50" : "border-gray-200 hover:border-gray-300",
                )}>
                <div className="flex items-center justify-between gap-2">
                  <div className="font-mono text-xs text-gray-900">{a.id}</div>
                  {a.active_override && <Badge>override</Badge>}
                </div>
                <div className="mt-1 text-[11px] text-gray-500">{a.plugin} / {a.purpose}</div>
              </button>
            ))}
          </CardBody>
        </Card>

        {asset && (
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>{asset.id}</CardTitle>
              </CardHeader>
              <CardBody className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  <Badge>v{asset.version}</Badge>
                  <Badge>{asset.plugin}</Badge>
                  {asset.variables.map(v => <Badge key={v}>{`{${v}}`}</Badge>)}
                </div>
                <Field label="Built-in template">
                  <Textarea rows={10} readOnly value={asset.template} />
                </Field>
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" icon={<RotateCcw className="h-4 w-4" />}
                    onClick={() => activeMut.mutate(null)}>
                    Use built-in
                  </Button>
                  <Button variant="secondary" size="sm" icon={<Plus className="h-4 w-4" />} onClick={startNew}>
                    New override
                  </Button>
                </div>
              </CardBody>
            </Card>

            <div className="grid grid-cols-1 xl:grid-cols-[280px_minmax(0,1fr)] gap-4">
              <Card>
                <CardHeader><CardTitle>Overrides</CardTitle></CardHeader>
                <CardBody className="space-y-2">
                  {asset.overrides?.length ? asset.overrides.map(o => (
                    <button key={o.id} type="button" onClick={() => setEditingId(o.id)}
                      className={clsx(
                        "w-full rounded-lg border px-3 py-2 text-left transition",
                        editingId === o.id ? "border-brand-500 bg-brand-50" : "border-gray-200 hover:border-gray-300",
                      )}>
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-sm font-medium text-gray-900 truncate">{o.name}</span>
                        {o.is_active && <CheckCircle className="h-4 w-4 text-emerald-600" />}
                      </div>
                    </button>
                  )) : <div className="text-sm text-gray-500">No overrides yet.</div>}
                </CardBody>
              </Card>

              <Card>
                <CardHeader><CardTitle>{editingId ? "Edit override" : "New override"}</CardTitle></CardHeader>
                <CardBody className="space-y-4">
                  <Field label="Name">
                    <Input value={name} onChange={e => setName(e.target.value)} />
                  </Field>
                  <Field label="Template">
                    <Textarea rows={14} value={template} onChange={e => setTemplate(e.target.value)} />
                  </Field>
                  <div className="flex flex-wrap justify-end gap-2">
                    {editingId && (
                      <Button variant="secondary" icon={<CheckCircle className="h-4 w-4" />}
                        onClick={() => activeMut.mutate(editingId)}>
                        Make active
                      </Button>
                    )}
                    <Button icon={<Save className="h-4 w-4" />}
                      loading={saveMut.isPending}
                      disabled={!name.trim() || !template.trim()}
                      onClick={() => saveMut.mutate()}>
                      Save
                    </Button>
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
