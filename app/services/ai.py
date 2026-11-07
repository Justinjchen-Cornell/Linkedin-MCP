import json

import httpx
from sqlmodel import Session, select

from app.models import CapturedPost
from app.services import ai_config
from app.services.settings import get_setting
from app.services.style_profile import build_style_profile


class AIConfigError(Exception):
    pass


def _chat(messages: list[dict], base_url: str, model: str, api_key: str) -> str:
    response = httpx.post(
        f"{base_url.rstrip('/')}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": model, "messages": messages, "temperature": 0.7},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def _parse_variants(content: str) -> list[dict]:
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return [{"title": "", "body": content[:3000], "hook_type": "unknown", "rationale": ""}]
    variants = data.get("variants") if isinstance(data, dict) else data
    if not isinstance(variants, list):
        return []
    normalized = []
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        normalized.append(
            {
                "title": str(variant.get("title", ""))[:200],
                "body": str(variant.get("body", ""))[:3000],
                "hook_type": str(variant.get("hook_type", "unknown"))[:40],
                "rationale": str(variant.get("rationale", ""))[:500],
            }
        )
    return normalized


def generate_variants(
    session: Session,
    topic: str,
    source_post_ids: list[int] | None = None,
    angle: str = "",
    language: str = "en",
    count: int = 3,
) -> dict:
    api_key = ai_config.get_api_key()
    if not api_key:
        raise AIConfigError("未配置 AI API Key，请到设置页填写。")

    base_url = get_setting(session, "ai_base_url", "https://api.deepseek.com")
    model = get_setting(session, "ai_model", "deepseek-chat")
    profile = build_style_profile(session)

    sources = []
    if source_post_ids:
        posts = session.exec(
            select(CapturedPost).where(CapturedPost.id.in_(source_post_ids))
        ).all()
        sources = [post.text[:1500] for post in posts if post.text]

    profile_text = (
        f"样本数 {profile['sample_count']}，平均长度 {profile['avg_chars']} 字符，"
        f"平均标签 {profile['hashtag_avg']} 个，emoji 比例 {profile['emoji_rate']}。\n"
        + "\n---\n".join(profile["samples"][:3])
    )
    system = (
        "你是 LinkedIn 资深内容编辑。只输出 JSON，不要解释。"
        "输出格式：{\"variants\":[{\"title\":\"\",\"body\":\"\",\"hook_type\":\"\",\"rationale\":\"\"}]}。"
        "每篇正文不超过 3000 字符，保留换行，不要虚构事实。"
    )
    user = (
        f"主题：{topic}\n角度：{angle or '自选'}\n语言：{language}\n生成 {count} 个不同版本。\n"
        f"我的历史风格：\n{profile_text}\n\n参考素材：\n" + "\n---\n".join(sources)
    )
    content = _chat(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        base_url,
        model,
        api_key,
    )
    return {"variants": _parse_variants(content), "style_profile": profile}
