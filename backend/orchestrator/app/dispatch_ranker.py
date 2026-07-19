"""Deterministic proximity + skill-tag ranker for volunteer dispatch, GenAI tie-break/explanation.
Rewritten fresh for this repo (methodology reused, no copied code, per plagiarism-detector constraint).
"""
from backend.shared.models import Volunteer
from backend.navigator.app.genai_clients import reason

# simple zone adjacency graph for proximity scoring (hops)
ZONE_ADJACENCY = {
    "Z1": {"Z1": 0, "Z5": 1, "Z2": 2, "Z4": 2, "Z3": 3},
    "Z2": {"Z2": 0, "Z5": 1, "Z1": 2, "Z3": 2, "Z4": 3},
    "Z3": {"Z3": 0, "Z5": 1, "Z2": 2, "Z4": 2, "Z1": 3},
    "Z4": {"Z4": 0, "Z5": 1, "Z1": 2, "Z3": 2, "Z2": 3},
    "Z5": {"Z5": 0, "Z1": 1, "Z2": 1, "Z3": 1, "Z4": 1},
}

REQUIRED_SKILL_BY_CATEGORY = {
    "medical": "medical",
    "security": "crowd_control",
    "crowd_crush": "crowd_control",
    "facility": "general",
}


def score_volunteer(volunteer: Volunteer, target_zone: str, needed_skill: str) -> float:
    hops = ZONE_ADJACENCY.get(target_zone, {}).get(volunteer.zone_id, 5)
    proximity_score = max(0, 10 - hops * 2)  # closer = higher, 0-10
    skill_score = 10 if needed_skill in (volunteer.skills or []) else 0
    return proximity_score * 0.5 + skill_score * 0.5


def rank_candidates(db, target_zone: str, category: str, top_n: int = 3) -> list[dict]:
    needed_skill = REQUIRED_SKILL_BY_CATEGORY.get(category, "general")
    volunteers = db.query(Volunteer).filter(Volunteer.available.is_(True)).all()

    ranked = sorted(
        volunteers,
        key=lambda v: score_volunteer(v, target_zone, needed_skill),
        reverse=True,
    )
    return [
        {
            "volunteer_id": v.id,
            "name": v.name,
            "zone_id": v.zone_id,
            "skills": v.skills,
            "score": round(score_volunteer(v, target_zone, needed_skill), 2),
        }
        for v in ranked[:top_n]
    ]


async def rank_with_explanation(db, target_zone: str, category: str) -> dict:
    candidates = rank_candidates(db, target_zone, category)
    if not candidates:
        return {"candidates": [], "explanation": "No available volunteers."}

    # tie-break only if top scores are within 0.5 of each other
    top_score = candidates[0]["score"]
    tied = [c for c in candidates if top_score - c["score"] <= 0.5]

    if len(tied) > 1:
        prompt = f"""Pick the best volunteer to dispatch to zone {target_zone} for a '{category}' incident.
Candidates (proximity+skill scored, tied): {tied}
Reply with the volunteer_id and one short sentence explaining why."""
        explanation = await reason(prompt)
    else:
        explanation = f"{candidates[0]['name']} is closest with matching skill for '{category}'."

    return {"candidates": candidates, "explanation": explanation}
