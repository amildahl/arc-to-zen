#!/usr/bin/env python3
"""User-facing entrypoint for the Arc to Zen desktop app."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from arc2zen.desktop import main


if __name__ == "__main__":
    raise SystemExit(main())
