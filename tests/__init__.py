import sys
from pathlib import Path

# Make the hlds package in src/ importable when running `python -m unittest` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
