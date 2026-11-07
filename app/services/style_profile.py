from sqlmodel import Session, select

from app.models import CapturedPost


def build_style_profile(session: Session) -> dict:
    posts = session.exec(
        select(CapturedPost)
        .where(CapturedPost.is_own == True)  # noqa: E712
        .order_by(CapturedPost.id.desc())
        .limit(50)
    ).all()
    texts = [post.text for post in posts if post.text]
    total_chars = sum(len(text) for text in texts)
    emoji_count = sum(1 for text in texts for char in text if ord(char) > 0x1F000)
    hashtag_count = sum(text.count("#") for text in texts)
    return {
        "sample_count": len(texts),
        "avg_chars": round(total_chars / len(texts)) if texts else 0,
        "emoji_rate": round(emoji_count / total_chars, 4) if total_chars else 0,
        "hashtag_avg": round(hashtag_count / len(texts), 1) if texts else 0,
        "samples": [text[:600] for text in texts[:5]],
    }
