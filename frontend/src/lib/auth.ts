import { create } from "zustand";
import { persist } from "zustand/middleware";
import { setAuthToken } from "./api";

type S = { token: string | null; setToken: (t: string | null) => void };

export const useAuth = create<S>()(persist((set) => ({
  token: null,
  setToken: (t) => { setAuthToken(t); set({ token: t }); },
}), { name: "airedteam-auth", onRehydrateStorage: () => (s) => { if (s?.token) setAuthToken(s.token); } }));
