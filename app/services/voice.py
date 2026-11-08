from sqlmodel import Session

from app.models import VoiceGuide


def get_voice_guide(session: Session) -> VoiceGuide:
    guide = session.get(VoiceGuide, 1)
    if guide is None:
        guide = VoiceGuide(id=1)
        session.add(guide)
        session.commit()
        session.refresh(guide)
    return guide


def voice_text(session: Session) -> str:
    guide = get_voice_guide(session)
    sections = [
        ("招牌观点", guide.beliefs),
        ("常用句式", guide.signature_phrases),
        ("禁用词/AI 腔", guide.banned_phrases),
        ("数据源", guide.data_sources),
        ("故事/案例", guide.stories),
    ]
    return "\n".join(f"{title}：{value}" for title, value in sections if value.strip())
