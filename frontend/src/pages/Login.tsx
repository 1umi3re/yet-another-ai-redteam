import { useEffect, useRef, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../lib/auth";
import { Card, CardBody } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Form";
import { Shield } from "lucide-react";
import { toast } from "sonner";
import { useI18n } from "../lib/i18n";
import { LanguageSwitch } from "../components/LanguageSwitch";

export default function Login() {
  const [pw, setPw] = useState("");
  const [loading, setLoading] = useState(false);
  const setToken = useAuth(s => s.setToken);
  const nav = useNavigate();
  const [searchParams] = useSearchParams();
  const { t } = useI18n();
  const requestedNext = searchParams.get("next");
  const next = requestedNext?.startsWith("/") ? requestedNext : "/dashboard";
  const expiredToastShown = useRef(false);

  useEffect(() => {
    if (searchParams.get("expired") === "1" && !expiredToastShown.current) {
      expiredToastShown.current = true;
      toast.error(t("Your session expired. Please sign in again."));
    }
  }, [searchParams, t]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const r = await api.post("/api/login", { password: pw });
      setToken(r.data.token);
      nav(next, { replace: true });
    } catch {
      toast.error(t("Invalid password"));
    } finally {
      setLoading(false);
    }
  }
  return (
    <div className="min-h-screen bg-gradient-to-br from-brand-50 via-gray-50 to-white flex items-center justify-center p-6">
      <div className="absolute right-6 top-6">
        <LanguageSwitch />
      </div>
      <div className="w-full max-w-sm">
        <div className="flex items-center gap-3 mb-6 justify-center">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white shadow-soft">
            <Shield className="h-5 w-5" />
          </div>
          <div>
            <div className="text-lg font-bold tracking-tight">airedteam</div>
            <div className="text-xs text-gray-500 -mt-0.5">{t("AI red-team console")}</div>
          </div>
        </div>
        <Card>
          <CardBody>
            <h1 className="text-base font-semibold mb-1">{t("Sign in")}</h1>
            <p className="text-sm text-gray-500 mb-5">{t("Enter your admin password to continue.")}</p>
            <form onSubmit={submit} className="space-y-3">
              <Input
                type="password"
                autoFocus
                placeholder={t("admin password")}
                value={pw}
                onChange={e => setPw(e.target.value)}
              />
              <Button type="submit" loading={loading} className="w-full justify-center">{t("Sign in")}</Button>
            </form>
          </CardBody>
        </Card>
        <p className="text-xs text-gray-400 text-center mt-4">
          {t("Configure AIREDTEAM_ADMIN_PASSWORD in your .env")}
        </p>
      </div>
    </div>
  );
}
