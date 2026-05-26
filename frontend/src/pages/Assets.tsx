import { useSearchParams } from "react-router-dom";
import { Database, FileText, Target } from "lucide-react";
import clsx from "clsx";

import Datasets from "./Datasets";
import PromptAssets from "./PromptAssets";
import { useI18n } from "../lib/i18n";

type AssetTab = "datasets" | "prompt-templates" | "attack-templates";

const tabs: Array<{ id: AssetTab; labelKey: string; icon: any }> = [
  { id: "datasets", labelKey: "Test Datasets", icon: Database },
  { id: "prompt-templates", labelKey: "Prompt Templates", icon: FileText },
  { id: "attack-templates", labelKey: "Attack Templates", icon: Target },
];

function isAttackTemplate(asset: any) {
  return asset?.purpose === "attack_template" || asset?.plugin === "attack_template";
}

function isPromptTemplate(asset: any) {
  return !isAttackTemplate(asset);
}

export default function Assets() {
  const { t } = useI18n();
  const [params, setParams] = useSearchParams();
  const selected = (params.get("tab") as AssetTab | null) ?? "datasets";
  const active = tabs.some(tab => tab.id === selected) ? selected : "datasets";

  const setActive = (tab: AssetTab) => {
    setParams(tab === "datasets" ? {} : { tab });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("Assets")}</h1>
        <p className="text-sm text-gray-500 mt-1">{t("Organize attack objectives and reusable prompt templates.")}</p>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-gray-200">
        {tabs.map(tab => {
          const Icon = tab.icon;
          const selectedTab = active === tab.id;
          return (
            <button key={tab.id} type="button" onClick={() => setActive(tab.id)}
              className={clsx(
                "inline-flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition",
                selectedTab ? "border-brand-600 text-brand-700" : "border-transparent text-gray-500 hover:text-gray-700",
              )}>
              <Icon className="h-4 w-4" />
              {t(tab.labelKey)}
            </button>
          );
        })}
      </div>

      {active === "datasets" && (
        <Datasets
          titleKey="Test Datasets"
          descriptionKey="Attack objective datasets store the goals that drive automated and manual tests."
        />
      )}
      {active === "prompt-templates" && (
        <PromptAssets
          titleKey="Prompt Templates"
          descriptionKey="LLM templates for executors, converters, evaluators, and judges. These templates are not sent to the tested LLM."
          listTitleKey="Prompt Templates"
          createTitleKey="Create prompt template"
          assetFilter={isPromptTemplate}
        />
      )}
      {active === "attack-templates" && (
        <PromptAssets
          titleKey="Attack Templates"
          descriptionKey="Target-facing prompt templates that combine with attack objectives before being sent to the tested LLM."
          listTitleKey="Attack Templates"
          createTitleKey="Create attack template"
          assetFilter={isAttackTemplate}
          idPrefix="attack_template"
          newAssetDefaults={{
            id: "attack_template.custom.v1",
            plugin: "attack_template",
            purpose: "attack_template",
            category: "Custom",
            variables: "prompt",
            template: "{prompt}",
          }}
        />
      )}
    </div>
  );
}
