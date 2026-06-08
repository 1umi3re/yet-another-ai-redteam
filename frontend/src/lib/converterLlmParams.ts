export type ConverterParamSchema = {
  type?: string;
  label?: string;
};

export type ConverterSchemas = Record<string, Record<string, ConverterParamSchema>>;

export type ConfiguredConverter = {
  plugin: string;
  params: Record<string, any>;
};

const CONVERTER_LLM_PARAM_KEYS = new Set(["converter_config_id", "translator_config_id"]);
const CONVERTER_LLM_LABELS = new Set(["Converter LLM", "Translator LLM"]);

export function getConverterLlmParamKeys(plugin: string, schemas: ConverterSchemas): string[] {
  return Object.entries(schemas[plugin] ?? {})
    .filter(([key, schema]) =>
      schema.type === "target_ref"
      && (CONVERTER_LLM_PARAM_KEYS.has(key) || CONVERTER_LLM_LABELS.has(schema.label ?? "")),
    )
    .map(([key]) => key);
}

export function countConvertersWithLlmConfig(
  converters: ConfiguredConverter[],
  schemas: ConverterSchemas,
): number {
  return converters.filter(converter => getConverterLlmParamKeys(converter.plugin, schemas).length > 0).length;
}

export function applyConverterLlmConfig(
  converters: ConfiguredConverter[],
  schemas: ConverterSchemas,
  configId: string,
): ConfiguredConverter[] {
  return converters.map(converter => {
    const llmParamKeys = getConverterLlmParamKeys(converter.plugin, schemas);
    if (llmParamKeys.length === 0) return converter;
    return {
      ...converter,
      params: {
        ...converter.params,
        ...Object.fromEntries(llmParamKeys.map(key => [key, configId])),
      },
    };
  });
}
