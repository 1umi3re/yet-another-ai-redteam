import { Field, Input, Select, Textarea } from "./ui/Form";
import { useI18n } from "../lib/i18n";

export type ParamSchema = {
  type: "bool" | "string" | "text" | "string_list" | "enum" | "target_ref" | "prompt_asset_ref";
  required?: boolean;
  default?: any;
  label?: string;
  help?: string;
  placeholder?: string;
  options?: string[];
  purpose_filter?: string;
  purpose_exclude?: string;
};

export type PluginSchemas = Record<string, Record<string, ParamSchema>>;
export type ConfiguredPlugin = { plugin: string; params: Record<string, any> };

export function defaultsFor(schema: Record<string, ParamSchema> | undefined): Record<string, any> {
  if (!schema) return {};
  const out: Record<string, any> = {};
  for (const [k, s] of Object.entries(schema)) {
    if (s.default !== undefined) out[k] = s.default;
    else if (s.type === "bool") out[k] = false;
    else if (s.type === "string_list") out[k] = [];
    else out[k] = "";
  }
  return out;
}

export function ParamField({
  name, schema, value, onChange, targets, promptAssets = [],
}: {
  name: string; schema: ParamSchema; value: any;
  onChange: (v: any) => void;
  targets: any[];
  promptAssets?: any[];
}) {
  const { t } = useI18n();
  const label = t(schema.label ?? name) + (schema.required ? " *" : "");
  const common = { label, hint: schema.help ? t(schema.help) : undefined } as const;
  switch (schema.type) {
    case "bool":
      return (
        <Field {...common}>
          <label className="inline-flex items-center gap-2 text-sm">
            <input type="checkbox" checked={!!value} onChange={e => onChange(e.target.checked)} />
            <span className="text-gray-600">{schema.help ? t(schema.help) : t("Enabled")}</span>
          </label>
        </Field>
      );
    case "enum":
      return (
        <Field {...common}>
          <Select value={value ?? ""} onChange={e => onChange(e.target.value)}>
            {(schema.options ?? []).map(o => <option key={o} value={o}>{o}</option>)}
          </Select>
        </Field>
      );
    case "target_ref":
      return (
        <Field {...common}>
          <Select value={value ?? ""} onChange={e => onChange(e.target.value)}>
            <option value="">{t("-- pick target --")}</option>
            {targets.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </Select>
        </Field>
      );
    case "prompt_asset_ref":
      const selectableAssets = schema.purpose_filter
        ? promptAssets.filter(a => a.purpose === schema.purpose_filter)
        : schema.purpose_exclude
        ? promptAssets.filter(a => a.purpose !== schema.purpose_exclude)
        : promptAssets;
      return (
        <Field {...common}>
          <Select value={value ?? ""} onChange={e => onChange(e.target.value)}>
            <option value="">{t("-- pick prompt asset --")}</option>
            {selectableAssets.map(a => (
              <option key={a.id} value={a.id}>
                {a.id}{a.source ? ` (${a.source})` : ""}
              </option>
            ))}
          </Select>
        </Field>
      );
    case "text":
      return (
        <Field {...common}>
          <Textarea rows={4} placeholder={schema.placeholder}
            value={value ?? ""} onChange={e => onChange(e.target.value)} />
        </Field>
      );
    case "string_list":
      return (
        <Field {...common} hint={`${schema.help ? t(schema.help) : ""} ${t("(one per line)")}`.trim()}>
          <Textarea rows={3} placeholder={schema.placeholder}
            value={Array.isArray(value) ? value.join("\n") : ""}
            onChange={e => onChange(e.target.value.split("\n").map(s => s.trim()).filter(Boolean))} />
        </Field>
      );
    case "string":
    default:
      return (
        <Field {...common}>
          <Input placeholder={schema.placeholder} value={value ?? ""}
            onChange={e => onChange(e.target.value)} />
        </Field>
      );
  }
}
