import clsx from "clsx";
import { KeyboardEvent, ReactNode } from "react";

export type TabItem<T extends string> = {
  id: T;
  label: ReactNode;
  icon?: ReactNode;
};

export function Tabs<T extends string>({
  tabs,
  value,
  onChange,
  idBase,
  children,
  className,
}: {
  tabs: Array<TabItem<T>>;
  value: T;
  onChange: (value: T) => void;
  idBase: string;
  children: (tab: T) => ReactNode;
  className?: string;
}) {
  const focusTab = (tabId: T) => {
    window.requestAnimationFrame(() => {
      document.getElementById(`${idBase}-${tabId}-tab`)?.focus();
    });
  };
  const handleKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    const lastIndex = tabs.length - 1;
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight") nextIndex = index === lastIndex ? 0 : index + 1;
    if (event.key === "ArrowLeft") nextIndex = index === 0 ? lastIndex : index - 1;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = lastIndex;
    if (nextIndex === null) return;
    event.preventDefault();
    const next = tabs[nextIndex];
    onChange(next.id);
    focusTab(next.id);
  };

  return (
    <div className={className}>
      <div role="tablist" className="flex flex-wrap gap-1 border-b border-gray-200">
        {tabs.map((tab, index) => {
          const selected = value === tab.id;
          const tabId = `${idBase}-${tab.id}-tab`;
          const panelId = `${idBase}-${tab.id}-panel`;
          return (
            <button
              key={tab.id}
              type="button"
              id={tabId}
              role="tab"
              aria-selected={selected}
              aria-controls={panelId}
              tabIndex={selected ? 0 : -1}
              onClick={() => onChange(tab.id)}
              onKeyDown={event => handleKeyDown(event, index)}
              className={clsx(
                "inline-flex items-center gap-2 border-b-2 px-4 py-2 -mb-px text-sm font-medium transition",
                selected
                  ? "border-brand-600 text-brand-700"
                  : "border-transparent text-gray-500 hover:text-gray-700",
              )}
            >
              {tab.icon}
              {tab.label}
            </button>
          );
        })}
      </div>

      {tabs.map(tab => {
        const selected = value === tab.id;
        return (
          <div
            key={tab.id}
            id={`${idBase}-${tab.id}-panel`}
            role="tabpanel"
            aria-labelledby={`${idBase}-${tab.id}-tab`}
            hidden={!selected}
            className="mt-6"
          >
            {selected ? children(tab.id) : null}
          </div>
        );
      })}
    </div>
  );
}
