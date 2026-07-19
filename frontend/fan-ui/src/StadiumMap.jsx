import { useEffect, useState } from "react";
import { Users } from "lucide-react";

const ZONES = [
  { id: "Z1", gate: "Gate A", side: "North", start: -45, end: 45 },
  { id: "Z2", gate: "Gate B", side: "East", start: 45, end: 135 },
  { id: "Z3", gate: "Gate C", side: "South", start: 135, end: 225 },
  { id: "Z4", gate: "Gate D", side: "West", start: 225, end: 315 },
];

const CX = 200;
const CY = 200;
const R_OUTER = 190;
const R_INNER = 120;

function polar(cx, cy, r, angleDeg) {
  const a = (angleDeg * Math.PI) / 180;
  return { x: cx + r * Math.sin(a), y: cy - r * Math.cos(a) };
}

function annulusPath(startAngle, endAngle, outer = R_OUTER, inner = R_INNER) {
  const p1 = polar(CX, CY, outer, endAngle);
  const p2 = polar(CX, CY, outer, startAngle);
  const p3 = polar(CX, CY, inner, startAngle);
  const p4 = polar(CX, CY, inner, endAngle);
  const largeArc = endAngle - startAngle > 180 ? 1 : 0;
  return `M ${p1.x} ${p1.y} A ${outer} ${outer} 0 ${largeArc} 0 ${p2.x} ${p2.y} L ${p3.x} ${p3.y} A ${inner} ${inner} 0 ${largeArc} 1 ${p4.x} ${p4.y} Z`;
}

function densityColor(density) {
  if (density == null) return "#3a5468"; // no data yet — muted steel
  if (density < 40) return "#2FA968"; // turf green (brighter for dark bg)
  if (density < 70) return "#F2A73B"; // amber
  return "#E5533B"; // crimson
}

function normalizeHeatmap(raw) {
  const out = {};
  if (!raw) return out;
  const list = Array.isArray(raw) ? raw : raw.zones || raw.data || [];
  for (const entry of list) {
    const id = entry.zone_id ?? entry.zone ?? entry.id;
    const val = entry.density_pct ?? entry.density ?? entry.crowd_density ?? entry.value;
    if (id != null && val != null) out[id] = val;
  }
  if (!Array.isArray(raw) && !raw.zones && !raw.data) {
    for (const [k, v] of Object.entries(raw)) {
      if (typeof v === "number") out[k] = v;
    }
  }
  return out;
}

export default function StadiumMap({ navigatorUrl, activeZones = [], onGateClick }) {
  const [densities, setDensities] = useState({});
  const [updatedAt, setUpdatedAt] = useState(null);
  const [error, setError] = useState(false);
  const [hovered, setHovered] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const res = await fetch(`${navigatorUrl}/heatmap`);
        const data = await res.json();
        if (!cancelled) {
          setDensities(normalizeHeatmap(data));
          setUpdatedAt(new Date());
          setError(false);
        }
      } catch {
        if (!cancelled) setError(true);
      }
    }

    poll();
    const interval = setInterval(poll, 20000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [navigatorUrl]);

  const focused = ZONES.find((z) => z.id === hovered);
  const infoZone = focused || ZONES.find((z) => activeZones.includes(z.id));
  const infoDensity = infoZone ? densities[infoZone.id] : null;

  return (
    <div className="rounded-2xl border border-[#2c4054] bg-[#0f2434] p-4 shadow-lg shadow-black/20">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-[Oswald] text-sm font-semibold uppercase tracking-wide text-[#F5F7F2]">
          Venue Map
        </h2>
        <span className="flex items-center gap-1 text-xs text-[#8fa3ac]">
          <Users size={13} />
          {error ? "offline" : "live"}
        </span>
      </div>

      <svg viewBox="0 0 400 400" className="w-full select-none" role="img" aria-label="Stadium map with gates and crowd zones">
        {ZONES.map((z) => {
          const density = densities[z.id];
          const isActive = activeZones.includes(z.id);
          const isHovered = hovered === z.id;
          const mid = (z.start + z.end) / 2;
          const gatePos = polar(CX, CY, R_OUTER + 22, mid);
          return (
            <g
              key={z.id}
              role="button"
              tabIndex={0}
              aria-label={`${z.gate}, ${z.side}, crowd ${density != null ? density + "%" : "unknown"}`}
              onMouseEnter={() => setHovered(z.id)}
              onMouseLeave={() => setHovered(null)}
              onFocus={() => setHovered(z.id)}
              onBlur={() => setHovered(null)}
              onClick={() => onGateClick?.(z.gate)}
              onKeyDown={(e) => e.key === "Enter" && onGateClick?.(z.gate)}
              style={{ cursor: "pointer" }}
            >
              <path
                d={annulusPath(z.start, z.end, isHovered ? R_OUTER + 6 : R_OUTER)}
                fill={densityColor(density)}
                opacity={isActive || isHovered ? 1 : 0.65}
                stroke={isActive ? "#F5F7F2" : isHovered ? "#F5F7F2" : "transparent"}
                strokeWidth={isActive ? 3 : isHovered ? 2 : 0}
                className={`transition-all duration-200 ${isActive ? "animate-pulse" : ""}`}
              />
              <circle
                cx={gatePos.x}
                cy={gatePos.y}
                r={isHovered ? 22 : 20}
                fill="#0B1C2C"
                stroke="#F5F7F2"
                strokeWidth={isHovered ? 2 : 1}
                className="transition-all duration-200"
              />
              <text
                x={gatePos.x}
                y={gatePos.y + 5}
                textAnchor="middle"
                fill="#F5F7F2"
                fontSize="16"
                fontWeight="700"
                fontFamily="Oswald, sans-serif"
                style={{ pointerEvents: "none" }}
              >
                {z.gate.slice(-1)}
              </text>
            </g>
          );
        })}
        {/* pitch */}
        <ellipse cx={CX} cy={CY} rx={R_INNER - 8} ry={R_INNER - 8} fill="#16513a" />
        <ellipse cx={CX} cy={CY} rx={R_INNER - 8} ry={R_INNER - 8} fill="none" stroke="#F5F7F2" strokeWidth="1.5" opacity="0.4" />
        <line x1={CX} y1={CY - (R_INNER - 8)} x2={CX} y2={CY + (R_INNER - 8)} stroke="#F5F7F2" strokeWidth="1.5" opacity="0.4" />
        <circle cx={CX} cy={CY} r={28} fill="none" stroke="#F5F7F2" strokeWidth="1.5" opacity="0.4" />
      </svg>

      {/* info panel — reflects hovered zone, or active zone from last answer */}
      <div className="mt-2 min-h-[44px] rounded-lg bg-[#0B1C2C] px-3 py-2 text-xs text-[#F5F7F2]">
        {infoZone ? (
          <div className="flex items-center justify-between">
            <span className="font-semibold">
              {infoZone.gate} · {infoZone.side} ({infoZone.id})
            </span>
            <span
              className="rounded-full px-2 py-0.5 font-semibold"
              style={{ background: densityColor(infoDensity), color: "#0B1C2C" }}
            >
              {infoDensity != null ? `${infoDensity}% crowd` : "no data"}
            </span>
          </div>
        ) : (
          <span className="text-[#8fa3ac]">Hover or tap a gate for live crowd details.</span>
        )}
      </div>

      <div className="mt-3 flex items-center justify-between text-[11px] text-[#8fa3ac]">
        <div className="flex gap-3">
          <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-[#2FA968]" />Low</span>
          <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-[#F2A73B]" />Medium</span>
          <span className="flex items-center gap-1"><i className="inline-block h-2 w-2 rounded-full bg-[#E5533B]" />High</span>
        </div>
        {updatedAt && <span>updated {updatedAt.toLocaleTimeString()}</span>}
      </div>
    </div>
  );
}