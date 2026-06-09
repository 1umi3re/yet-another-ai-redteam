import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../lib/auth";
import { Shield, Target, Database, PlayCircle, ListChecks, LogOut, Sparkles, MessageSquare, Tags } from "lucide-react";
import clsx from "clsx";
import { useI18n } from "../lib/i18n";
import { LanguageSwitch } from "./LanguageSwitch";

const nav = [
  { to: "/dashboard", labelKey: "Dashboard", icon: Sparkles },
  { to: "/targets",   labelKey: "Targets",   icon: Target },
  { to: "/assets",    labelKey: "Assets",    icon: Database },
  { to: "/attack-methods", labelKey: "Attack Methods", icon: Tags },
  { to: "/runs/new",  labelKey: "New run",   icon: PlayCircle },
  { to: "/runs",      labelKey: "Runs",      icon: ListChecks },
  { to: "/manual",    labelKey: "Manual Console", icon: MessageSquare },
];

export default function Layout() {
  const setToken = useAuth(s => s.setToken);
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useI18n();

  const isNavActive = (to: string) => {
    const path = location.pathname;
    if (to === "/runs/new") return path === "/runs/new";
    if (to === "/runs") return path === "/runs" || (path.startsWith("/runs/") && path !== "/runs/new");
    if (to === "/assets") return path === "/assets" || path === "/datasets" || path === "/prompt-assets";
    return path === to;
  };

  return (
    <div className="h-[100dvh] max-h-[100dvh] min-h-0 flex overflow-hidden bg-gray-50">
      <aside className="h-full w-60 shrink-0 overflow-hidden bg-white border-r border-gray-200 flex flex-col">
        <div className="h-16 flex items-center gap-2 px-5 border-b border-gray-100">
          <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-soft">
            <Shield className="h-4 w-4" />
          </div>
          <div>
            <div className="text-sm font-bold tracking-tight">airedteam</div>
            <div className="text-[10px] text-gray-500 -mt-0.5">{t("AI redteam console")}</div>
          </div>
        </div>
        <nav className="p-3 space-y-0.5 flex-1 min-h-0">
          {nav.map(({ to, labelKey, icon: Icon }) => {
            const active = isNavActive(to);
            return (
              <Link key={to} to={to} aria-current={active ? "page" : undefined} className={clsx(
                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition",
                active ? "bg-brand-50 text-brand-700 font-medium" : "text-gray-700 hover:bg-gray-100"
              )}>
                <Icon className="h-4 w-4" />
                {t(labelKey)}
              </Link>
            );
          })}
        </nav>
        <div className="p-3 border-t border-gray-100 space-y-2">
          <LanguageSwitch />
          <button
            className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-gray-700 hover:bg-gray-100"
            onClick={() => { setToken(null); navigate("/login"); }}
          >
            <LogOut className="h-4 w-4" /> {t("Sign out")}
          </button>
        </div>
      </aside>
      <main className="flex-1 min-h-0 min-w-0 flex flex-col overflow-hidden">
        <div className="flex-1 min-h-0 overflow-auto">
          <div className="max-w-6xl min-w-0 mx-auto px-8 py-8">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
