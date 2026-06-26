type Params = Record<string, any>;

export type ConfiguredConverter = {
  plugin: string;
  params: Params;
  [key: string]: any;
};

export type AttackMethodTemplate = {
  id: string;
  asset_id: string;
  is_builtin: boolean;
};

export type AttackMethodTemplateDetail = {
  is_template_backed: boolean;
  default_asset_id: string | null;
  templates: AttackMethodTemplate[];
};

export function expandConverterWithAttackTemplates(
  converter: ConfiguredConverter,
  detail: AttackMethodTemplateDetail | null | undefined,
): ConfiguredConverter[] {
  if (!detail?.is_template_backed || !detail.default_asset_id || !detail.templates.length) {
    return [{ ...converter, params: { ...converter.params } }];
  }
  return detail.templates.map(template => {
    const params = { ...converter.params };
    delete params.attack_template_override_id;
    delete params.attack_template_use_builtin;
    params.attack_template_asset_id = template.asset_id || detail.default_asset_id;
    if (template.is_builtin) {
      params.attack_template_use_builtin = true;
    } else {
      params.attack_template_override_id = template.id;
    }
    return { ...converter, params };
  });
}

type LoadAttackMethodTemplateDetail = (plugin: string) => Promise<AttackMethodTemplateDetail | null | undefined>;

function cloneRef<T extends Record<string, any>>(ref: T): T {
  return { ...ref, params: { ...(ref.params ?? {}) } };
}

async function expandConverterRef<T extends ConfiguredConverter>(
  ref: T,
  loadTemplateDetail: LoadAttackMethodTemplateDetail,
): Promise<T[]> {
  if (!ref?.plugin) return [cloneRef(ref)];
  const detail = await loadTemplateDetail(ref.plugin);
  return expandConverterWithAttackTemplates(ref, detail) as T[];
}

export async function expandRunSpecAttackTemplates<T extends Record<string, any>>(
  runspec: T,
  loadTemplateDetail: LoadAttackMethodTemplateDetail,
): Promise<T> {
  const next: Record<string, any> = { ...runspec };

  if (Array.isArray(runspec.converters)) {
    const expandedConverters = await Promise.all(
      runspec.converters.map((ref: ConfiguredConverter) => expandConverterRef(ref, loadTemplateDetail)),
    );
    next.converters = expandedConverters.flat();
  }

  if (Array.isArray(runspec.executors)) {
    const expandedExecutors = await Promise.all(
      runspec.executors.map((ref: Record<string, any>) => {
        if (ref?.kind !== "converter_method") return Promise.resolve([cloneRef(ref)]);
        return expandConverterRef(ref as ConfiguredConverter, loadTemplateDetail);
      }),
    );
    next.executors = expandedExecutors.flat();
  }

  return next as T;
}
