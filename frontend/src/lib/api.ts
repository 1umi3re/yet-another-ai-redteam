import axios from "axios";

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

let unauthorizedHandler: (() => void) | null = null;

export function setAuthToken(t: string | null) {
  if (t) api.defaults.headers.common["Authorization"] = `Bearer ${t}`;
  else delete api.defaults.headers.common["Authorization"];
}

export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler;
}

function isLoginRequest(url: string | undefined): boolean {
  return !!url && url.endsWith("/api/login");
}

api.interceptors.response.use(
  response => response,
  error => {
    if (error?.response?.status === 401 && !isLoginRequest(error.config?.url)) {
      setAuthToken(null);
      unauthorizedHandler?.();
    }
    return Promise.reject(error);
  },
);
