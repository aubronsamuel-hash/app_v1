import { api } from "../lib/api";

export async function login(username: string, password: string) {
  const res = await api("/auth/token-json", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  localStorage.setItem("token", res.access_token);
  return res;
}

export async function register(username: string, password: string) {
  return api("/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export async function me() {
  return api("/auth/me");
}

export function logout() {
  localStorage.removeItem("token");
}
