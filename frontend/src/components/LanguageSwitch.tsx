import { Globe } from "lucide-react";

import { useI18n } from "../lib/i18n";

export function LanguageSwitch({ compact = false }: { compact?: boolean }) {
  const { language, toggleLanguage, t } = useI18n();
  const next = language === "en" ? "中文" : "English";
  return (
    <button
      type="button"
      onClick={toggleLanguage}
      title={t("Language")}
      aria-label={t("Language")}
      className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-medium text-gray-700 shadow-sm transition hover:bg-gray-50"
    >
      <Globe className="h-4 w-4" />
      {!compact && <span>{next}</span>}
    </button>
  );
}
