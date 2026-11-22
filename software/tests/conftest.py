"""Thomas's software tests: import software/ modules and the repo-root app modules, headless."""
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))            # software/
sys.path.insert(0, str(HERE.parent.parent))     # repo root (filters, metrics)
