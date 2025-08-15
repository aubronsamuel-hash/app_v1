import { useState, useEffect } from "react";
import { useAuth } from "./hooks/useAuth";
import { listMissions, createMission } from "./services/missions";

function App() {
  const { token, login, logout } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [missions, setMissions] = useState<any[]>([]);

  useEffect(() => {
    if (!token) return;
    listMissions()
      .then((r) => {
        const items = Array.isArray(r) ? r : r.items;
        setMissions(items || []);
      })
      .catch(console.error);
  }, [token]);

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    try {
      await login(username, password);
      setUsername("");
      setPassword("");
    } catch (err) {
      console.error(err);
    }
  }

  async function handleNew() {
    const now = new Date();
    const later = new Date(now.getTime() + 2 * 60 * 60 * 1000);
    const m = {
      title: "Demo",
      start: now.toISOString(),
      end: later.toISOString(),
      status: "draft",
      positions: [{ label: "SON", count: 1, skills: {} }],
    };
    try {
      await createMission(m);
      const r = await listMissions();
      const items = Array.isArray(r) ? r : r.items;
      setMissions(items || []);
    } catch (err) {
      console.error(err);
    }
  }

  return (
    <div>
      <header>
        {token ? (
          <button onClick={logout}>Logout</button>
        ) : (
          <form onSubmit={handleLogin}>
            <input
              placeholder="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
            <input
              placeholder="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <button type="submit">Login</button>
          </form>
        )}
      </header>
      {token && (
        <main>
          <h2>Missions</h2>
          <button onClick={handleNew}>New mission</button>
          <ul>
            {missions.map((m, i) => (
              <li key={m.id || i}>{m.title || JSON.stringify(m)}</li>
            ))}
          </ul>
        </main>
      )}
    </div>
  );
}

export default App;
