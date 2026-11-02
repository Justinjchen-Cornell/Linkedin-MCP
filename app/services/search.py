from sqlalchemy import text
from sqlmodel import Session

from app.models import CapturedPost


def index_post(session: Session, post: CapturedPost) -> None:
    session.execute(
        text("DELETE FROM captured_posts_fts WHERE rowid = :id"),
        {"id": post.id},
    )
    session.execute(
        text(
            "INSERT INTO captured_posts_fts(rowid, text, author_name) "
            "VALUES (:id, :text, :author_name)"
        ),
        {"id": post.id, "text": post.text, "author_name": post.author_name},
    )


def search_post_ids(session: Session, q: str) -> list[int]:
    q = q.strip()
    if not q:
        return []
    if len(q) >= 3:
        phrase = '"' + q.replace('"', '""') + '"'
        try:
            rows = session.execute(
                text(
                    "SELECT rowid FROM captured_posts_fts "
                    "WHERE captured_posts_fts MATCH :q"
                ),
                {"q": phrase},
            ).all()
            ids = [row[0] for row in rows]
            if ids:
                return ids
        except Exception:
            pass
    rows = session.execute(
        text(
            "SELECT id FROM captured_posts "
            "WHERE text LIKE :q OR author_name LIKE :q"
        ),
        {"q": f"%{q}%"},
    ).all()
    return [row[0] for row in rows]
