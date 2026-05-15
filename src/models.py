from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Item:
    url: str
    title: str
    content: str
    published_at: datetime
    source: str
    raw: dict = field(default_factory=dict)
