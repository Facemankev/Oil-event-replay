"""Fixed public publisher registry; no arbitrary destinations or credentials."""
import json
from pathlib import Path
SOURCES = json.loads(Path(__file__).with_name("registry.json").read_text())
MAX_BYTES = 4 * 1024 * 1024
