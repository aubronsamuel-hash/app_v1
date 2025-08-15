import { useState } from "react";
import * as auth from "../services/auth";

export function useAuth() {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem("token"));

  async function login(username: string, password: string) {
    const res = await auth.login(username, password);
    setToken(localStorage.getItem("token"));
    return res;
  }

  function logout() {
    auth.logout();
    setToken(null);
  }

  return { token, login, logout, me: auth.me };
}
