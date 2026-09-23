"""Run the source checkout without an editable installation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from pixel_coloring.app import main

raise SystemExit(main())
