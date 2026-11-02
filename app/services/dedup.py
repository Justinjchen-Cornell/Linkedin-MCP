import hashlib
from urllib.parse import urlsplit, urlunsplit

from app.schemas.capture import CapturedPostIn


def normalize_url(url: str | None) -> str | None:
    if not url:
        return None
    parts = urlsplit(url.strip())
    path = parts.path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def content_hash(post: CapturedPostIn) -> str:
    text = " ".join(post.text.split())
    key = (post.author_url or post.author_name or "") + "\n" + text
    return hashlib.sha256(key.encode("utf-8")).hexdigest()


def dedup_key(post: CapturedPostIn) -> tuple[str, str]:
    if post.urn:
        return ("urn", post.urn)
    normalized = normalize_url(post.url)
    if normalized:
        return ("url", normalized)
    return ("hash", content_hash(post))
