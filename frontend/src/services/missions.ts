import { api } from "../lib/api";

export async function listMissions() {
  return api("/missions");
}

export async function createMission(m: any) {
  return api("/missions", {
    method: "POST",
    body: JSON.stringify(m),
  });
}
