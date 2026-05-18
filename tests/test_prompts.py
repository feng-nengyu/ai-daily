from pathlib import Path

import pytest

from src.prompts import load_prompt, render


def test_load_prompt_finds_file(tmp_path: Path):
    (tmp_path / "score.txt").write_text("hi {keywords}", encoding="utf-8")
    out = load_prompt("score", prompts_dir=tmp_path)
    assert out == "hi {keywords}"


def test_load_prompt_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_prompt("nope", prompts_dir=tmp_path)


def test_render_fills_placeholders():
    tmpl = "kw={keywords} t={title}"
    out = render(tmpl, {"keywords": "LLM, agent", "title": "Hello"})
    assert out == "kw=LLM, agent t=Hello"


def test_render_preserves_literal_braces_in_json_examples():
    # JSON in prompts uses {{ and }} to mean literal { } under str.format
    tmpl = 'Output: {{"score": 7}} for {title}'
    out = render(tmpl, {"title": "x"})
    assert out == 'Output: {"score": 7} for x'


def test_render_missing_key_raises():
    with pytest.raises(KeyError):
        render("hi {missing}", {})
