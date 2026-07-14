import { useEffect } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { api } from "../lib/api";
import {
  Shield,
  Target,
  Database,
  PlayCircle,
  ListChecks,
  LogOut,
  Sparkles,
  MessageSquare,
  Tags,
  Settings as SettingsIcon,
  Radar,
} from "lucide-react";
import clsx from "clsx";
import { useI18n } from "../lib/i18n";
import { LanguageSwitch } from "./LanguageSwitch";

const nav = [
  { to: "/dashboard", labelKey: "Dashboard", icon: Sparkles },
  { to: "/targets",   labelKey: "Targets",   icon: Target },
  { to: "/reconnaissance", labelKey: "Reconnaissance", icon: Radar },
  { to: "/assets",    labelKey: "Assets",    icon: Database },
  { to: "/attack-methods", labelKey: "Attack Methods", icon: Tags },
  { to: "/runs/new",  labelKey: "New run",   icon: PlayCircle },
  { to: "/runs",      labelKey: "Runs",      icon: ListChecks },
  { to: "/manual",    labelKey: "Manual Console", icon: MessageSquare },
  { to: "/settings",  labelKey: "Settings", icon: SettingsIcon },
];

const assetSubnav = [
  { to: "/assets?tab=datasets", tab: "datasets", labelKey: "Test Datasets" },
  { to: "/assets?tab=prompt-templates", tab: "prompt-templates", labelKey: "Prompt Templates" },
  { to: "/assets?tab=attack-templates", tab: "attack-templates", labelKey: "Attack Templates" },
];

export default function Layout() {
  const setToken = useAuth(s => s.setToken);
  const token = useAuth(s => s.token);
  const account = useAuth(s => s.account);
  const setAccount = useAuth(s => s.setAccount);
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useI18n();

  useEffect(() => {
    if (!token || account) return;
    api.get("/api/auth/me").then(response => setAccount(response.data)).catch(() => undefined);
  }, [account, setAccount, token]);

  const isNavActive = (to: string) => {
    const path = location.pathname;
    if (to === "/runs/new") return path === "/runs/new";
    if (to === "/runs") return path === "/runs" || (path.startsWith("/runs/") && path !== "/runs/new");
    if (to === "/assets") return path === "/assets" || path === "/datasets" || path === "/prompt-assets";
    return path === to;
  };
  const activeAssetTab = new URLSearchParams(location.search).get("tab") ?? "datasets";

  return (
    <div className="h-[100dvh] max-h-[100dvh] min-h-0 flex overflow-hidden bg-gray-50">
      <aside className="h-full w-60 shrink-0 overflow-hidden bg-white border-r border-gray-200 flex flex-col">
        <div className="h-16 shrink-0 flex items-center gap-2 px-5 border-b border-gray-100">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-soft">
            <Shield className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight">airedteam</div>
            <div className="text-[10px] text-gray-500 -mt-0.5">{t("AI redteam console")}</div>
          </div>
        </div>
        <nav className="flex-1 min-h-0 overflow-y-auto overscroll-contain p-3 space-y-0.5">
          {nav.map(({ to, labelKey, icon: Icon }) => {
            const active = isNavActive(to);
            return (
              <div key={to}>
                <Link to={to} aria-current={active ? "page" : undefined} className={clsx(
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition",
                  active ? "bg-brand-50 text-brand-700 font-medium" : "text-gray-700 hover:bg-gray-100"
                )}>
                  <Icon className="h-4 w-4" />
                  {t(labelKey)}
                </Link>
                {to === "/assets" && active && (
                  <div className="mt-1 ml-6 space-y-0.5 border-l border-gray-100 pl-2">
                    {assetSubnav.map(item => {
                      const itemActive = location.pathname === "/assets" && activeAssetTab === item.tab;
                      return (
                        <Link
                          key={item.tab}
                          to={item.to}
                          aria-current={itemActive ? "page" : undefined}
                          className={clsx(
                            "block rounded-md px-2 py-1.5 text-xs transition",
                            itemActive
                              ? "bg-brand-50 text-brand-700 font-medium"
                              : "text-gray-500 hover:bg-gray-100 hover:text-gray-700",
                          )}
                        >
                          {t(item.labelKey)}
                        </Link>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </nav>
        <div className="shrink-0 bg-white p-3 border-t border-gray-100 space-y-1">
          {account && (
            <div className="flex items-center gap-2.5 px-3 py-2 min-w-0">
              {account.picture ? (
                <img src={account.picture} alt="" referrerPolicy="no-referrer" className="h-8 w-8 rounded-full object-cover" />
              ) : (
                <div className="h-8 w-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center text-xs font-semibold">
                  {account.display_name.slice(0, 1).toUpperCase()}
                </div>
              )}
              <div className="min-w-0">
                <div className="truncate text-xs font-medium text-gray-800">{account.display_name}</div>
                <div className="truncate text-[10px] text-gray-500">{account.email ?? t("Administrator")}</div>
              </div>
            </div>
          )}
          <LanguageSwitch variant="sidebar" />
          <button
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-gray-700 transition hover:bg-gray-100"
            onClick={() => { setToken(null); navigate("/login"); }}
          >
            <LogOut className="h-4 w-4" /> {t("Sign out")}
          </button>
        </div>
      </aside>
      <main className="flex-1 min-h-0 min-w-0 flex flex-col overflow-hidden">
        <div className="flex-1 min-h-0 overflow-auto">
          <div className="max-w-[88rem] min-w-0 mx-auto px-8 py-8">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
