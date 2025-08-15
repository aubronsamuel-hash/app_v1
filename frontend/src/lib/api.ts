export const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

function authHeader(): HeadersInit {
  const t = localStorage.getItem("token");
  return t ? { Authorization: "Bearer " + t } : {};
}

export async function api(path: string, init: RequestInit = {}) {
  const r = await fetch(API_URL + path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
      ...authHeader(),
    },
  });
  if (!r.ok) throw new Error("HTTP " + r.status);
  return r.status === 204 ? null : r.json();
}
