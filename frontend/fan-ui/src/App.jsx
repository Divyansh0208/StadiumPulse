import { useEffect, useRef, useState } from "react";
import { Send, Loader2, Accessibility, Map as MapIcon, X } from "lucide-react";
import StadiumMap from "./StadiumMap.jsx";

const NAVIGATOR_URL = import.meta.env.VITE_NAVIGATOR_URL || "http://localhost:8001";

const LANGS = [
  { code: "en", label: "EN" },
  { code: "es", label: "ES" },
  { code: "fr", label: "FR" },
  { code: "hi", label: "HI" },
  { code: "ar", label: "AR" },
];

const QUICK_PROMPTS = [
  "Where is the nearest restroom?",
  "Where is the nearest first aid station?",
  "Where can I find food and drinks?",
  "What are the accessible routes?",
];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [lang, setLang] = useState("en");
  const [accessibilityMode, setAccessibilityMode] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showMap, setShowMap] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  async function ask(query) {
    if (!query.trim()) return;
    setMessages((m) => [...m, { role: "user", text: query }]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${NAVIGATOR_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, lang, accessibility_mode: accessibilityMode }),
      });
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", text: data.answer, sources: data.sources || [] }]);
    } catch {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: "Connection error — the navigator service isn't reachable right now.", sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  }

  function handleSubmit(e) {
    e.preventDefault();
    ask(input);
  }

  function handleGateClick(gateLabel) {
    setShowMap(false);
    ask(`What's near ${gateLabel}?`);
  }

  const lastAssistant = [...messages].reverse().find((m) => m.role === "assistant");
  const activeZones = (lastAssistant?.sources || []).filter((s) => /^Z\d+$/.test(s));

  const fontSize = accessibilityMode ? "1.1rem" : "1rem";
  const touchTarget = accessibilityMode ? "3.25rem" : "2.75rem";

  return (
    <div className="min-h-screen bg-[#0B1C2C]" style={{ fontSize }}>
      {/* header */}
      <header className="border-b border-[#1c3247] bg-[#0B1C2C] px-4 py-4 text-[#F5F7F2] sm:px-6">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <div>
            <h1 className="font-[Oswald] text-xl font-bold uppercase tracking-wide sm:text-2xl">
              StadiumPulse
            </h1>
            <p className="flex items-center gap-1.5 text-xs text-[#8fa3ac] sm:text-sm">
              <span className="h-1.5 w-1.5 rounded-full bg-[#2FA968] animate-pulse" />
              Fan Navigator — live wayfinding
            </p>
          </div>
          <button
            onClick={() => setShowMap((s) => !s)}
            className="flex items-center gap-1.5 rounded-full border border-[#2c4054] bg-[#132a3d] px-3 py-2 text-xs font-medium text-[#F5F7F2] md:hidden"
          >
            {showMap ? <X size={14} /> : <MapIcon size={14} />}
            {showMap ? "Close" : "Map"}
          </button>
        </div>
      </header>

      <main className="mx-auto grid max-w-5xl gap-4 p-4 sm:p-6 md:grid-cols-[1fr_320px]">
        {/* chat column */}
        <section className={`${showMap ? "hidden" : "flex"} md:flex flex-col`}>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <div className="flex gap-1 rounded-full border border-[#2c4054] bg-[#132a3d] p-1">
              {LANGS.map((l) => (
                <button
                  key={l.code}
                  onClick={() => setLang(l.code)}
                  className={`rounded-full px-3 py-1.5 text-xs font-semibold transition-colors ${
                    lang === l.code ? "bg-[#2FA968] text-[#0B1C2C]" : "text-[#8fa3ac] hover:text-[#F5F7F2]"
                  }`}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setAccessibilityMode((a) => !a)}
              aria-pressed={accessibilityMode}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${
                accessibilityMode
                  ? "border-[#2FA968] bg-[#2FA968] text-[#0B1C2C]"
                  : "border-[#2c4054] bg-[#132a3d] text-[#8fa3ac]"
              }`}
            >
              <Accessibility size={14} />
              Accessibility mode
            </button>
          </div>

          <div
            ref={scrollRef}
            className="flex-1 space-y-3 overflow-y-auto rounded-2xl border border-[#2c4054] bg-[#0f2434] p-4"
            style={{ minHeight: 360, maxHeight: 480 }}
          >
            {messages.length === 0 && (
              <div>
                <p className="mb-3 text-sm text-[#8fa3ac]">
                  Ask about gates, seating, restrooms, accessibility, or crowd conditions.
                </p>
                <div className="flex flex-wrap gap-2">
                  {QUICK_PROMPTS.map((q) => (
                    <button
                      key={q}
                      onClick={() => ask(q)}
                      className="rounded-full border border-[#2c4054] bg-[#132a3d] px-3 py-1.5 text-xs font-medium text-[#F5F7F2] hover:bg-[#1c3a52]"
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div className="max-w-[80%]">
                  <div
                    className={
                      m.role === "user"
                        ? "rounded-2xl rounded-br-sm bg-[#2FA968] px-4 py-2.5 text-[#0B1C2C]"
                        : "rounded-2xl rounded-bl-sm border border-[#2c4054] bg-[#132a3d] px-4 py-2.5 text-[#F5F7F2]"
                    }
                  >
                    {m.text}
                  </div>
                  {m.role === "assistant" && m.sources?.length > 0 && (
                    <div className="mt-1.5 flex flex-wrap gap-1.5">
                      {m.sources.map((s) => (
                        <span
                          key={s}
                          className="rounded-full bg-[#F5F7F2]/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-[#8fa3ac]"
                        >
                          {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center gap-2 text-sm text-[#8fa3ac]">
                <Loader2 size={14} className="animate-spin" />
                Thinking…
              </div>
            )}
          </div>

          <form onSubmit={handleSubmit} className="mt-3 flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type your question…"
              style={{ height: touchTarget, fontSize }}
              className="flex-1 rounded-full border border-[#2c4054] bg-[#132a3d] px-4 text-[#F5F7F2] placeholder:text-[#5f7683] focus:outline-none focus:ring-2 focus:ring-[#2FA968]"
            />
            <button
              type="submit"
              style={{ height: touchTarget, width: touchTarget }}
              className="flex items-center justify-center rounded-full bg-[#2FA968] text-[#0B1C2C] transition-colors hover:bg-[#26925a] disabled:opacity-40"
              disabled={loading || !input.trim()}
              aria-label="Send"
            >
              <Send size={18} />
            </button>
          </form>
        </section>

        {/* map column */}
        <aside className={`${showMap ? "block" : "hidden"} md:block`}>
          <StadiumMap navigatorUrl={NAVIGATOR_URL} activeZones={activeZones} onGateClick={handleGateClick} />
        </aside>
      </main>
    </div>
  );
}