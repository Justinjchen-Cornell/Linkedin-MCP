from urllib.parse import quote_plus


def build_search_url(kind: str, value: str) -> str:
    if kind == "keyword":
        return (
            "https://www.linkedin.com/search/results/content/"
            f"?keywords={quote_plus(value)}"
            "&datePosted=%22past-week%22"
            "&sortBy=%22date_posted%22"
        )
    if kind == "hashtag":
        tag = value.lstrip("#").strip()
        return f"https://www.linkedin.com/feed/hashtag/?keywords={quote_plus(tag)}"
    raise ValueError(f"unsupported watchlist kind: {kind}")
