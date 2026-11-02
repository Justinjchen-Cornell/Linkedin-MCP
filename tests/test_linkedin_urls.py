from app.services.linkedin_urls import build_search_url


def test_keyword_url_encodes_and_filters_week():
    url = build_search_url("keyword", "AI 内容运营")
    assert "keywords=AI+%E5%86%85%E5%AE%B9%E8%BF%90%E8%90%A5" in url
    assert "datePosted=%22past-week%22" in url


def test_hashtag_url_strips_hash():
    assert build_search_url("hashtag", "#B2B") == "https://www.linkedin.com/feed/hashtag/?keywords=B2B"
