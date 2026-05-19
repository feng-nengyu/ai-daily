from src.notifier.labels import label_for


def test_known_lab_source():
    lbl = label_for("rss:openai-blog")
    assert lbl.short == "OpenAI"
    assert lbl.category == "lab"


def test_known_github_trending():
    lbl = label_for("github:github-trending-agent")
    assert lbl.short == "GitHub · agent"
    assert lbl.category == "github"


def test_known_arxiv():
    lbl = label_for("arxiv:arxiv-cs-ai")
    assert lbl.short == "arXiv"
    assert lbl.category == "paper"


def test_known_hn():
    lbl = label_for("hackernews:hackernews-ai")
    assert lbl.short == "Hacker News"
    assert lbl.category == "community"


def test_unknown_rss_falls_back_to_name_and_other():
    lbl = label_for("rss:some-new-blog")
    assert lbl.short == "some-new-blog"
    assert lbl.category == "other"


def test_unknown_github_falls_back_to_github_category():
    lbl = label_for("github:github-trending-rust")
    assert lbl.short == "github-trending-rust"
    assert lbl.category == "github"


def test_completely_unstructured_source():
    lbl = label_for("nopfx")
    assert lbl.short == "nopfx"
    assert lbl.category == "other"
