"""Correlates crowd/transport/incident signals per zone -> severity-ranked recommended actions.
Deterministic correlation + severity scoring; GenAI only generates the human-readable action text.
"""
from backend.navigator.app.genai_clients import reason
from .agents import crowd_agent, transport_agent, incident_agent

ALL_ZONES = ["Z1", "Z2", "Z3", "Z4", "Z5"]


def correlate(db) -> list[dict]:
    crowd = crowd_agent.read_signal(db)
    transport = transport_agent.read_signal(db)
    incident = incident_agent.read_signal(db)

    correlated = []
    for zone_id in ALL_ZONES:
        c = crowd.get(zone_id, {})
        t = transport.get(zone_id, {})
        i = incident.get(zone_id, {})

        if not (c.get("alert") or t.get("alert") or i.get("alert")):
            continue

        crowd_score = (c.get("density_pct", 0) / 100) * 10
        transport_score = min(t.get("delay_minutes", 0) / 20, 1) * 10
        incident_score = (i.get("max_severity", 0) / 5) * 10

        score = max(crowd_score, transport_score, incident_score)
        secondary = (crowd_score + transport_score + incident_score) - score
        score = min(score + secondary * 0.15, 10.0)

        correlated.append(
            {
                "zone_id": zone_id,
                "severity": round(score, 1),
                "signals": {"crowd": c, "transport": t, "incident": i},
            }
        )

    correlated.sort(key=lambda x: x["severity"], reverse=True)
    return correlated


async def generate_action_text(zone_id: str, signals: dict) -> str:
    prompt = f"""You are a stadium ops assistant. Given correlated signals for zone {zone_id}, write ONE short
recommended action for staff (max 2 sentences, imperative tone). Be specific and operational.

Signals: {signals}

Recommended action:"""
    return await reason(prompt)


async def build_recommended_actions(db) -> list[dict]:
    correlated = correlate(db)
    actions = []
    for item in correlated:
        text = await generate_action_text(item["zone_id"], item["signals"])
        actions.append({**item, "action_text": text})
    return actions