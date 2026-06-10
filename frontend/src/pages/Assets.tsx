import { useSearchParams } from "react-router-dom";
import { Database, FileText, Target } from "lucide-react";

import Datasets from "./Datasets";
import PromptAssets from "./PromptAssets";
import { useI18n } from "../lib/i18n";
import { Tabs, TabItem } from "../components/ui/Tabs";

type AssetTab = "datasets" | "prompt-templates" | "attack-templates";

const tabConfig: Array<{ id: AssetTab; labelKey: string; icon: any }> = [
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
  const active = tabConfig.some(tab => tab.id === selected) ? selected : "datasets";

  const setActive = (tab: AssetTab) => {
    setParams(tab === "datasets" ? {} : { tab });
  };
  const tabs: Array<TabItem<AssetTab>> = tabConfig.map(tab => {
    const Icon = tab.icon;
    return {
      id: tab.id,
      label: t(tab.labelKey),
      icon: <Icon className="h-4 w-4" />,
    };
  });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{t("Assets")}</h1>
        <p className="text-sm text-gray-500 mt-1">{t("Organize attack objectives and reusable prompt templates.")}</p>
      </div>

      <Tabs tabs={tabs} value={active} onChange={setActive} idBase="assets">
        {tab => {
          if (tab === "datasets") {
            return (
              <Datasets
                headingLevel="h2"
                titleKey="Test Datasets"
                descriptionKey="Attack objective datasets store the goals that drive automated and manual tests."
              />
            );
          }
          if (tab === "prompt-templates") {
            return (
              <PromptAssets
                headingLevel="h2"
                titleKey="Prompt Templates"
                descriptionKey="LLM templates for executors, converters, evaluators, and judges. These templates are not sent to the tested LLM."
                listTitleKey="Prompt Templates"
                createTitleKey="Create prompt template"
                newAssetButtonKey="New asset"
                saveAssetButtonKey="Save"
                assetFilter={isPromptTemplate}
              />
            );
          }
          return (
            <PromptAssets
              headingLevel="h2"
              titleKey="Attack Templates"
              descriptionKey="Target-facing prompt templates that combine with attack objectives before being sent to the tested LLM."
              listTitleKey="Attack Templates"
              createTitleKey="Create attack template"
              newAssetButtonKey="New attack template"
              saveAssetButtonKey="Save attack template"
              assetFilter={isAttackTemplate}
              idPrefix="attack_template"
              newAssetDefaults={{
                id: "",
                plugin: "attack_template",
                purpose: "attack_template",
                category: "Custom",
                variables: "prompt",
                template: "{prompt}",
              }}
            />
          );
        }}
      </Tabs>
    </div>
  );
}
