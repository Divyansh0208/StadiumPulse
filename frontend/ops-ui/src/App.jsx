import { useEffect, useState } from "react";
import { LogIn, RefreshCw, ChevronDown, AlertTriangle, ShieldAlert, CheckCircle2 } from "lucide-react";

const ORCH_URL = import.meta.env.VITE_ORCHESTRATOR_URL || "http://localhost:8002";

function severity(sev) {
  if (sev >= 7) return { color: "#E5533B", label: "High", icon: ShieldAlert };
  if (sev >= 4) return { color: "#F2A73B", label: "Medium", icon: AlertTriangle };
  return { color: "#2FA968", label: "Low", icon: CheckCircle2 };
}

export default function App() {
  const [token, setToken] = useState(null);
  const [actions, setActions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loginError, setLoginError] = useState("");
  const [creds, setCreds] = useState({ username: "staff", password: "demo" });
  const [updatedAt, setUpdatedAt] = useState(null);
  const [openSignals, setOpenSignals] = useState({});

  async function login(e) {
    e.preventDefault();
    setLoginError("");
    try {
      const res = await fetch(`${ORCH_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(creds),
      });
      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
      } else {
        setLoginError("Invalid username or password.");
      }
    } catch {
      setLoginError("Can't reach the orchestrator service.");
    }
  }

  async function tickAndFetch() {
    if (!token) return;
    setLoading(true);
    const headers = { Authorization: `Bearer ${token}` };
    try {
      await fetch(`${ORCH_URL}/simulate/tick`, { method: "POST", headers });
      const res = await fetch(`${ORCH_URL}/actions`, { headers });
      const data = await res.json();
      setActions(data);
      setUpdatedAt(new Date());
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token) return;
    tickAndFetch();
    const interval = setInterval(tickAndFetch, 8000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  if (!token) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0B1C2C] px-4">
        <div className="w-full max-w-sm rounded-2xl border border-[#2c4054] bg-[#0f2434] p-8 shadow-lg shadow-black/30">
          <h1 className="font-[Oswald] text-2xl font-bold uppercase tracking-wide text-[#F5F7F2]">
            StadiumPulse
          </h1>
          <p className="mb-6 text-sm text-[#8fa3ac]">Ops Orchestrator — staff sign in</p>

          <form onSubmit={login} className="flex flex-col gap-3">
            <input
              value={creds.username}
              onChange={(e) => setCreds({ ...creds, username: e.target.value })}
              placeholder="Username"
              className="h-11 rounded-lg border border-[#2c4054] bg-[#132a3d] px-3 text-[#F5F7F2] placeholder:text-[#5f7683] focus:outline-none focus:ring-2 focus:ring-[#2FA968]"
            />
            <input
              type="password"
              value={creds.password}
              onChange={(e) => setCreds({ ...creds, password: e.target.value })}
              placeholder="Password"
              className="h-11 rounded-lg border border-[#2c4054] bg-[#132a3d] px-3 text-[#F5F7F2] placeholder:text-[#5f7683] focus:outline-none focus:ring-2 focus:ring-[#2FA968]"
            />
            {loginError && <p className="text-xs text-[#E5533B]">{loginError}</p>}
            <button
              type="submit"
              className="mt-1 flex h-11 items-center justify-center gap-2 rounded-lg bg-[#2FA968] font-semibold text-[#0B1C2C] transition-colors hover:bg-[#26925a]"
            >
              <LogIn size={16} />
              Log in
            </button>
          </form>
          <p className="mt-4 text-xs text-[#5f7683]">Demo credentials: staff / demo</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B1C2C]">
      <header className="border-b border-[#1c3247] px-4 py-4 sm:px-6">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <div>
            <h1 className="font-[Oswald] text-xl font-bold uppercase tracking-wide text-[#F5F7F2] sm:text-2xl">
              StadiumPulse
            </h1>
            <p className="flex items-center gap-1.5 text-xs text-[#8fa3ac] sm:text-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-[#2FA968] animate-pulse" />
              Ops Dashboard — recommended actions
            </p>
          </div>
          <button
            onClick={tickAndFetch}
            disabled={loading}
            className="flex items-center gap-1.5 rounded-full border border-[#2c4054] bg-[#132a3d] px-3 py-2 text-xs font-medium text-[#F5F7F2] transition-colors hover:bg-[#1c3a52] disabled:opacity-50"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            {loading ? "Refreshing" : "Refresh now"}
          </button>
        </div>
      </header>

      <main className="mx-auto max-w-4xl p-4 sm:p-6">
        {updatedAt && (
          <p className="mb-3 text-xs text-[#5f7683]">Last updated {updatedAt.toLocaleTimeString()}</p>
        )}

        {actions.length === 0 && !loading && (
          <div className="rounded-2xl border border-[#2c4054] bg-[#0f2434] p-6 text-center">
            <CheckCircle2 className="mx-auto mb-2 text-[#2FA968]" size={28} />
            <p className="font-semibold text-[#F5F7F2]">All zones nominal</p>
            <p className="text-sm text-[#8fa3ac]">No active alerts right now.</p>
          </div>
        )}

        <div className="flex flex-col gap-3">
          {actions.map((a) => {
            const sev = severity(a.severity);
            const Icon = sev.icon;
            const isOpen = openSignals[a.zone_id];
            return (
              <div
                key={a.zone_id}
                className="rounded-2xl border bg-[#0f2434] p-4"
                style={{ borderColor: sev.color, borderWidth: 1.5 }}
              >
                <div className="flex items-center justify-between">
                  <span className="font-[Oswald] font-semibold uppercase tracking-wide text-[#F5F7F2]">
                    Zone {a.zone_id}
                  </span>
                  <span
                    className="flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold"
                    style={{ background: sev.color, color: "#0B1C2C" }}
                  >
                    <Icon size={13} />
                    {sev.label} · {a.severity}
                  </span>
                </div>
                <p className="mt-2 text-sm text-[#dbe4e1]">{a.action_text}</p>

                <button
                  onClick={() => setOpenSignals((s) => ({ ...s, [a.zone_id]: !s[a.zone_id] }))}
                  className="mt-3 flex items-center gap-1 text-xs font-medium text-[#8fa3ac] hover:text-[#F5F7F2]"
                >
                  <ChevronDown size={14} className={`transition-transform ${isOpen ? "rotate-180" : ""}`} />
                  Source signals
                </button>
                {isOpen && (
                  <pre className="mt-2 overflow-x-auto rounded-lg bg-[#0B1C2C] p-3 text-xs text-[#8fa3ac]">
                    {JSON.stringify(a.signals, null, 2)}
                  </pre>
                )}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}