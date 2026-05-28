from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
DEFAULT_CONFIG = ROOT / "config" / "default.yaml"
REPORTS_DIR = ROOT / "reports"
IMAGES_DIR = ROOT / "docs" / "images"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

