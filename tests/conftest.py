"""Shared test setup: run headless and import the app modules from the repo root."""
import os
import sys
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")          # no plot windows during tests
os.environ.setdefault("GRIPCHECK_SIMULATE", "1")    # tests use simulated data unless a test switches to a device
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
