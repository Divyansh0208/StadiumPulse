from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.shared.seed import get_embedder


def retrieve(db: Session, query: str, k: int = 4):
    embedder = get_embedder()
    q_emb = embedder.encode([query], normalize_embeddings=True)[0].tolist()

    rows = db.execute(
        text(
            """
            SELECT zone_id, kind, text, meta,
                   1 - (embedding <=> :qemb) AS score
            FROM venue_chunks
            ORDER BY embedding <=> :qemb
            LIMIT :k
            """
        ),
        {"qemb": str(q_emb), "k": k},
    ).mappings().all()
    return [dict(r) for r in rows]
