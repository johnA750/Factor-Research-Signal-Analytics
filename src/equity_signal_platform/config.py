from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PlatformConfig:
    """Container for YAML configuration values."""

    raw: dict[str, Any]

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PlatformConfig":
        with Path(path).open("r", encoding="utf-8") as file:
            raw = yaml.safe_load(file)
        return cls(raw=raw)

    def section(self, name: str) -> dict[str, Any]:
        return dict(self.raw.get(name, {}))

