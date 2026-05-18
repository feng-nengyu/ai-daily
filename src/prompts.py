from pathlib import Path


def load_prompt(name: str, prompts_dir: Path = Path("prompts")) -> str:
    path = Path(prompts_dir) / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render(template: str, values: dict) -> str:
    """Render a str.format template. JSON examples must escape braces as {{ }}.

    KeyError propagates if a {placeholder} has no matching value — caller
    catches & logs so prompt bugs surface loudly during dev.
    """
    return template.format(**values)
