"""Fixed, reviewed policy. No data-dependent threshold fitting."""
import json
from pathlib import Path
from event_history.library import require
from world_events.events import digest

HERE = Path(__file__).resolve().parent
POLICY = json.loads((HERE / 'policy.json').read_text())
require(digest(POLICY) == (HERE / 'POLICY.sha256').read_text().strip(),
        'Signal policy changed; review and register a new version before evaluating')
