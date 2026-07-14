import { create } from "zustand";
import { persist } from "zustand/middleware";
import { setAuthToken, setUnauthorizedHandler } from "./api";

export type Account = {
  subject: string;
  display_name: string;
  email: string | null;
  picture: string | null;
  auth_method: "password" | "oidc" | string;
};

type S = {
  token: string | null;
  account: Account | null;
  setToken: (t: string | null) => void;
  setAccount: (account: Account | null) => void;
  setSession: (token: string, account: Account) => void;
};

export const useAuth = create<S>()(persist((set) => ({
  token: null,
  account: null,
  setToken: (t) => { setAuthToken(t); set({ token: t, ...(!t ? { account: null } : {}) }); },
  setAccount: (account) => set({ account }),
  setSession: (token, account) => { setAuthToken(token); set({ token, account }); },
}), { name: "airedteam-auth", onRehydrateStorage: () => (s) => { if (s?.token) setAuthToken(s.token); } }));

setUnauthorizedHandler(() => {
  useAuth.getState().setToken(null);
  if (window.location.pathname === "/login") return;
  const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  window.location.assign(`/login?expired=1&next=${encodeURIComponent(next)}`);
});
