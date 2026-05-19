"""Friendly display label + category mapping for raw `Item.source` strings.

Storage stores source like "rss:openai-blog" or "github:github-trending-agent".
The web template wants both:
- a short human label ("OpenAI", "GitHub: agent")
- a category for color-coding ("lab", "expert", ...)
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SourceLabel:
    short: str
    category: str  # one of: lab / framework / expert / media / github / paper / community / other


_REGISTRY: dict[str, SourceLabel] = {
    # 主要厂商 / 实验室
    "rss:openai-blog":        SourceLabel("OpenAI",          "lab"),
    "rss:deepmind-blog":      SourceLabel("DeepMind",        "lab"),
    "rss:google-research":    SourceLabel("Google Research", "lab"),
    "rss:nvidia-dev-blog":    SourceLabel("NVIDIA",          "lab"),
    "rss:microsoft-research": SourceLabel("MS Research",     "lab"),
    "rss:together-ai-blog":   SourceLabel("Together AI",     "lab"),
    "rss:huggingface-blog":   SourceLabel("Hugging Face",    "lab"),
    # 框架
    "rss:langchain-blog":     SourceLabel("LangChain",       "framework"),
    # 个人专家 / 通讯
    "rss:simon-willison":     SourceLabel("Simon Willison",   "expert"),
    "rss:lilian-weng":        SourceLabel("Lilian Weng",      "expert"),
    "rss:sebastian-raschka":  SourceLabel("Sebastian Raschka","expert"),
    "rss:andrej-karpathy":    SourceLabel("Karpathy",         "expert"),
    "rss:import-ai":          SourceLabel("Import AI",        "expert"),
    # 中文媒体
    "rss:qbitai":             SourceLabel("量子位",            "media"),
    # GitHub trending
    "github:github-trending-agent": SourceLabel("GitHub · agent", "github"),
    "github:github-trending-llm":   SourceLabel("GitHub · llm",   "github"),
    "github:github-trending-mcp":   SourceLabel("GitHub · mcp",   "github"),
    # arXiv
    "arxiv:arxiv-cs-ai":      SourceLabel("arXiv",            "paper"),
    # HN
    "hackernews:hackernews-ai": SourceLabel("Hacker News",    "community"),
}

# Fallback category by prefix when source isn't in _REGISTRY.
_PREFIX_FALLBACK: dict[str, str] = {
    "rss": "other",
    "github": "github",
    "arxiv": "paper",
    "hackernews": "community",
}


def label_for(source: str) -> SourceLabel:
    """Return the friendly label for a raw source string. Unknown sources get
    a best-effort label derived from the prefix and a category guess."""
    hit = _REGISTRY.get(source)
    if hit is not None:
        return hit
    # Unknown: parse "prefix:name"
    if ":" in source:
        prefix, name = source.split(":", 1)
        category = _PREFIX_FALLBACK.get(prefix, "other")
        return SourceLabel(short=name, category=category)
    return SourceLabel(short=source, category="other")
