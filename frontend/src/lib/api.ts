import axios from "axios";

export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000" });

export function setAuthToken(t: string | null) {
  if (t) api.defaults.headers.common["Authorization"] = `Bearer ${t}`;
  else delete api.defaults.headers.common["Authorization"];
}
