from pathlib import Path
from tabwright.reddit import extract_reddit

FIXTURE = (Path(__file__).parent / "fixtures" / "reddit_post.html").read_text()
URL = "https://www.reddit.com/r/learnpython/comments/abc123/how_do_i_reverse/"


def test_extracts_title():
    result = extract_reddit(FIXTURE, URL)
    assert "How do I reverse a list in Python?" in result["content"]


def test_extracts_post_body():
    result = extract_reddit(FIXTURE, URL)
    assert "list.reverse()" in result["content"]


def test_extracts_comments():
    result = extract_reddit(FIXTURE, URL)
    assert "commenter1" in result["content"]
    assert "my_list[::-1]" in result["content"]
    assert "commenter2" in result["content"]
    assert "iterator" in result["content"]


def test_includes_score_and_author():
    result = extract_reddit(FIXTURE, URL)
    assert "1234" in result["content"]
    assert "testuser" in result["content"]


def test_content_type_is_reddit():
    result = extract_reddit(FIXTURE, URL)
    assert result["content_type"] == "reddit"


def test_url_preserved():
    result = extract_reddit(FIXTURE, URL)
    assert result["url"] == URL
