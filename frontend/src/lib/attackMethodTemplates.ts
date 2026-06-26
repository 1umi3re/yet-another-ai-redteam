type Params = Record<string, any>;

export type ConfiguredConverter = {
  plugin: string;
  params: Params;
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
    return [{ plugin: converter.plugin, params: { ...converter.params } }];
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
    return { plugin: converter.plugin, params };
  });
}
