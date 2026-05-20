import { create } from "zustand";
import { persist } from "zustand/middleware";
import { setAuthToken, setUnauthorizedHandler } from "./api";

type S = { token: string | null; setToken: (t: string | null) => void };

export const useAuth = create<S>()(persist((set) => ({
  token: null,
  setToken: (t) => { setAuthToken(t); set({ token: t }); },
}), { name: "airedteam-auth", onRehydrateStorage: () => (s) => { if (s?.token) setAuthToken(s.token); } }));

setUnauthorizedHandler(() => {
  useAuth.getState().setToken(null);
  if (window.location.pathname === "/login") return;
  const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
  window.location.assign(`/login?expired=1&next=${encodeURIComponent(next)}`);
});
