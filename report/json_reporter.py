"""
report/json_reporter.py
-----------------------
Saves the gap evaluation report as a structured JSON file.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class JSONReporter:
    def __init__(self, output_dir: str = "output"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, evaluation: dict[str, Any], filename: str = None) -> str:
        if not filename:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            org = evaluation.get("organization", "org").replace(" ", "_")
            filename = f"csf_gap_report_{org}_{ts}.json"

        path = self._output_dir / filename
        with open(path, "w") as f:
            json.dump(evaluation, f, indent=2)
        return str(path)
