import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { LogIn, Shield } from "lucide-react";
import { toast } from "sonner";
import { api } from "../lib/api";
import { Account, useAuth } from "../lib/auth";
import { Card, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Form";
import { useI18n } from "../lib/i18n";
import { LanguageSwitch } from "../components/LanguageSwitch";

type AuthConfig = {
  oidc_enabled: boolean;
  oidc_forced: boolean;
  password_enabled: boolean;
  oidc_start_url: string | null;
};

type LoginResult = { token: string; account: Account; next: string };

function safeNext(value: string | null) {
  return value?.startsWith("/") && !value.startsWith("//") ? value : "/dashboard";
}

export default function Login() {
  const [pw, setPw] = useState("");
  const [loading, setLoading] = useState(false);
  const [oidcLoading, setOidcLoading] = useState(false);
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const setSession = useAuth(s => s.setSession);
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useI18n();
  const next = safeNext(searchParams.get("next"));
  const expiredToastShown = useRef(false);
  const oidcErrorShown = useRef(false);
  const exchangeStarted = useRef(false);

  useEffect(() => {
    api.get<AuthConfig>("/api/auth/config")
      .then(response => setConfig(response.data))
      .catch(() => toast.error(t("Failed to load authentication options")));
  }, [t]);

  useEffect(() => {
    if (searchParams.get("expired") === "1" && !expiredToastShown.current) {
      expiredToastShown.current = true;
      toast.error(t("Your session expired. Please sign in again."));
    }
    if (searchParams.get("oidc_error") && !oidcErrorShown.current) {
      oidcErrorShown.current = true;
      toast.error(t("OIDC authentication failed. Please try again."));
    }
  }, [searchParams, t]);

  useEffect(() => {
    const ticket = searchParams.get("oidc_ticket");
    if (!ticket || exchangeStarted.current) return;
    exchangeStarted.current = true;
    setOidcLoading(true);
    api.post<LoginResult>("/api/auth/oidc/exchange", { ticket })
      .then(({ data }) => {
        setSession(data.token, data.account);
        nav(safeNext(data.next), { replace: true });
      })
      .catch(() => {
        toast.error(t("OIDC login expired or was already used."));
        nav(`/login?next=${encodeURIComponent(next)}`, { replace: true });
      })
      .finally(() => setOidcLoading(false));
  }, [nav, next, searchParams, setSession, t]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!config?.password_enabled) return;
    setLoading(true);
    try {
      const response = await api.post<LoginResult>("/api/login", { password: pw });
      setSession(response.data.token, response.data.account);
      nav(next, { replace: true });
    } catch (error: any) {
      if (error?.response?.status === 403) toast.error(t("Password login is disabled by policy."));
      else toast.error(t("Invalid password"));
    } finally {
      setLoading(false);
    }
  }

  function startOIDC() {
    if (!config?.oidc_start_url) return;
    setOidcLoading(true);
    const base = new URL(api.defaults.baseURL || window.location.origin, window.location.origin);
    const url = new URL(config.oidc_start_url, base);
    url.searchParams.set("next", next);
    window.location.assign(url.toString());
  }

  const forced = config?.oidc_forced === true;
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-gray-50 to-white flex items-center justify-center p-6">
      <div className="absolute right-6 top-6"><LanguageSwitch /></div>
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-6 justify-center">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-soft">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight">airedteam</div>
            <div className="text-xs text-gray-500 -mt-0.5">{t("AI redteam console")}</div>
          </div>
        </div>
        <Card>
          <CardBody>
            <h1 className="text-base font-semibold mb-1">{t("Sign in")}</h1>
            {config?.oidc_enabled && (
              <div className="mt-5">
                <Button
                  type="button"
                  icon={<LogIn className="h-4 w-4" />}
                  loading={oidcLoading}
                  className="w-full justify-center"
                  onClick={startOIDC}
                >
                  {t("Sign in with OIDC")}
                </Button>
              </div>
            )}
            {config?.oidc_enabled && (
              <div className="my-5 flex items-center gap-3 text-xs text-gray-400">
                <div className="h-px flex-1 bg-gray-200" />{t("or use admin password")}<div className="h-px flex-1 bg-gray-200" />
              </div>
            )}
            <p className="text-sm text-gray-500 mb-5">
              {forced
                ? t("Password authentication is disabled. Use your organization account above.")
                : t("Enter your admin password to continue.")}
            </p>
            <form onSubmit={submit} className="space-y-3">
              <Input
                type="password"
                autoFocus={!config?.oidc_enabled}
                placeholder={t("admin password")}
                value={pw}
                disabled={forced || !config}
                onChange={e => setPw(e.target.value)}
              />
              <Button
                type="submit"
                loading={loading}
                disabled={forced || !config}
                className="w-full justify-center"
              >
                {forced ? t("Password login disabled") : t("Sign in")}
              </Button>
            </form>
          </CardBody>
        </Card>
        <p className="text-xs text-gray-400 text-center mt-4">
          {forced
            ? t("OIDC authentication is required by policy")
            : t("Configure AIREDTEAM_ADMIN_PASSWORD in your .env")}
        </p>
      </div>
    </div>
  );
}
