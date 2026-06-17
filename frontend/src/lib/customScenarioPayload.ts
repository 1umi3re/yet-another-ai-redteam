type Params = Record<string, any>;

export type CustomScenarioExecutor = {
  kind: "executor" | "converter_method";
  plugin: string;
  params: Params;
};

export type CustomScenarioPlugin = {
  plugin: string;
  params: Params;
};

export type BuildCustomScenarioPayloadInput = {
  scenarioName: string;
  description: string;
  tagsText: string;
  nativeExecutors: CustomScenarioExecutor[];
  converters: CustomScenarioPlugin[];
  scorer: CustomScenarioPlugin;
  generalMultiTurnExecutors: string[];
  goalSource: "dataset_items" | "fixed";
  samplingEnabled: boolean;
  samplingLimit: string;
  samplingShuffle: boolean;
  samplingSeed: string;
  timeoutSeconds: string;
};

export type CustomScenarioPayload = {
  name: string;
  description: string;
  tags: string[];
  template: {
    version: 2;
    executors: CustomScenarioExecutor[];
    scorers: CustomScenarioPlugin[];
    sampling?: {
      limit: number | null;
      shuffle: boolean;
      seed: number | null;
    };
    timeout_seconds?: number;
  };
};

function parseOptionalInt(value: string): number | null {
  const trimmed = value.trim();
  if (!trimmed) return null;
  const parsed = parseInt(trimmed, 10);
  return Number.isFinite(parsed) ? parsed : null;
}

function parseOptionalFloat(value: string): number | undefined {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const parsed = parseFloat(trimmed);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function parseTags(tagsText: string): string[] {
  return tagsText
    .split(",")
    .map(tag => tag.trim())
    .filter(Boolean);
}

export function buildCustomScenarioPayload(input: BuildCustomScenarioPayloadInput): CustomScenarioPayload {
  const generalMultiTurnExecutors = new Set(input.generalMultiTurnExecutors);
  const executors: CustomScenarioExecutor[] = [
    ...input.nativeExecutors.map(ex => {
      const params = { ...ex.params };
      if (generalMultiTurnExecutors.has(ex.plugin) && input.goalSource === "dataset_items") {
        params.goal = "";
      }
      return { kind: "executor" as const, plugin: ex.plugin, params };
    }),
    ...input.converters.map(converter => ({
      kind: "converter_method" as const,
      plugin: converter.plugin,
      params: { ...converter.params },
    })),
  ];

  const template: CustomScenarioPayload["template"] = {
    version: 2,
    executors,
    scorers: [{ plugin: input.scorer.plugin, params: { ...input.scorer.params } }],
  };

  if (input.samplingEnabled) {
    template.sampling = {
      limit: parseOptionalInt(input.samplingLimit),
      shuffle: input.samplingShuffle,
      seed: input.samplingShuffle ? parseOptionalInt(input.samplingSeed) : null,
    };
  }

  const timeout = parseOptionalFloat(input.timeoutSeconds);
  if (timeout !== undefined) template.timeout_seconds = timeout;

  return {
    name: input.scenarioName.trim(),
    description: input.description.trim(),
    tags: parseTags(input.tagsText),
    template,
  };
}
