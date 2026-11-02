import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlmodel import Session, select

from app.models import CapturedPost, Comment, Person
from app.schemas.capture import CapturePayload, CapturedPostIn
from app.services.dedup import content_hash, dedup_key, normalize_url
from app.services.settings import get_setting


@dataclass
class IngestResult:
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    post_ids: list[int] = field(default_factory=list)


def _find_existing(session: Session, post: CapturedPostIn) -> CapturedPost | None:
    kind, value = dedup_key(post)
    if kind == "urn":
        return session.exec(select(CapturedPost).where(CapturedPost.urn == value)).first()
    if kind == "url":
        exact = session.exec(select(CapturedPost).where(CapturedPost.url == post.url)).first()
        if exact:
            return exact
        for candidate in session.exec(select(CapturedPost)).all():
            if normalize_url(candidate.url) == value:
                return candidate
        return None
    return session.exec(
        select(CapturedPost).where(CapturedPost.content_hash == value)
    ).first()


def _upsert_person(
    session: Session,
    name: str,
    url: str | None,
    headline: str | None,
    now: datetime,
) -> None:
    if not name and not url:
        return
    person = None
    if url:
        person = session.exec(select(Person).where(Person.url == url)).first()
    if person is None and name:
        person = session.exec(
            select(Person).where(Person.name == name, Person.url == None)  # noqa: E711
        ).first()
    if person is None:
        person = Person(
            name=name,
            url=url,
            headline=headline,
            first_seen_at=now,
            last_seen_at=now,
        )
    else:
        person.name = name or person.name
        person.headline = headline or person.headline
        person.last_seen_at = now
    session.add(person)


def _ingest_comment(session: Session, post_id: int, comment, now: datetime) -> None:
    existing = session.exec(
        select(Comment).where(
            Comment.post_id == post_id,
            Comment.author_url == comment.author_url,
            Comment.text == comment.text,
        )
    ).first()
    if existing:
        existing.reactions = max(existing.reactions, comment.reactions)
        existing.captured_at = now
        session.add(existing)
        return
    session.add(
        Comment(
            post_id=post_id,
            author_name=comment.author_name,
            author_url=comment.author_url,
            text=comment.text,
            created_at=comment.created_at,
            reactions=comment.reactions,
            captured_at=now,
        )
    )


def ingest_capture(session: Session, payload: CapturePayload) -> IngestResult:
    result = IngestResult()
    now = datetime.now(timezone.utc)
    own_url = normalize_url(get_setting(session, "own_profile_url"))

    for post in payload.posts:
        if not post.text.strip() and not post.author_name.strip():
            result.skipped += 1
            continue

        is_own = bool(own_url and normalize_url(post.author_url) == own_url)
        existing = _find_existing(session, post)

        if existing is None:
            record = CapturedPost(
                urn=post.urn,
                url=post.url,
                author_name=post.author_name,
                author_url=post.author_url,
                author_headline=post.author_headline,
                text=post.text,
                posted_at=post.posted_at,
                reactions=post.reactions,
                comments_count=post.comments_count,
                reposts=post.reposts,
                media_json=json.dumps(post.media, ensure_ascii=False),
                source=post.source,
                keyword=post.keyword,
                raw_html=post.raw_html,
                content_hash=content_hash(post),
                is_own=is_own,
                first_captured_at=now,
                last_captured_at=now,
            )
            session.add(record)
            session.flush()
            result.inserted += 1
            post_id = record.id
        else:
            existing.reactions = max(existing.reactions, post.reactions)
            existing.comments_count = max(existing.comments_count, post.comments_count)
            existing.reposts = max(existing.reposts, post.reposts)
            existing.text = post.text or existing.text
            existing.author_name = existing.author_name or post.author_name
            existing.author_url = existing.author_url or post.author_url
            existing.author_headline = existing.author_headline or post.author_headline
            existing.raw_html = post.raw_html or existing.raw_html
            existing.content_hash = content_hash(post)
            existing.is_own = is_own or existing.is_own
            existing.last_captured_at = now
            session.add(existing)
            result.updated += 1
            post_id = existing.id

        result.post_ids.append(post_id)
        _upsert_person(session, post.author_name, post.author_url, post.author_headline, now)
        for comment in post.comments:
            _ingest_comment(session, post_id, comment, now)
            _upsert_person(session, comment.author_name, comment.author_url, None, now)

    session.commit()
    return result
