"""
profiler/meridian_client.py
---------------------------
Pulls live data from the Meridian Risk Scoring API to auto-populate
CSF 2.0 subcategory evidence for Identify and Detect functions.
"""

from __future__ import annotations
import logging
from typing import Any

import httpx
from config import settings

logger = logging.getLogger("csf_profiler.meridian")


class MeridianClient:
    def __init__(self, base_url: str = None):
        self._base = (base_url or settings.meridian_api_url).rstrip("/")
        self._timeout = settings.meridian_timeout

    def _get(self, path: str) -> Any:
        try:
            r = httpx.get(f"{self._base}{path}", timeout=self._timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            logger.warning(f"Meridian API unavailable ({exc}) — skipping integration")
            return None

    def is_available(self) -> bool:
        result = self._get("/health")
        return result is not None and result.get("neo4j_connected", False)

    def get_assets(self) -> list[dict]:
        result = self._get("/assets")
        return result or []

    def get_control_gaps(self) -> dict:
        result = self._get("/controls/gaps")
        return result or {"total_gaps": 0, "gaps": []}

    def get_asset_risk(self, asset_id: str) -> dict | None:
        return self._get(f"/assets/{asset_id}/risk")

    def summarize_for_csf(self) -> dict[str, Any]:
        """
        Summarize Meridian data into CSF-relevant evidence.
        Returns a dict used to auto-populate subcategory maturity scores.
        """
        if not self.is_available():
            return {"available": False}

        assets = self.get_assets()
        gaps = self.get_control_gaps()

        n_assets = len(assets)
        n_scored = sum(1 for a in assets if a.get("risk_score") is not None)
        avg_risk = (
            sum(a["risk_score"] for a in assets if a.get("risk_score"))
            / max(n_scored, 1)
        )
        n_gaps = gaps.get("total_gaps", 0)
        high_risk = [a for a in assets if (a.get("risk_score") or 0) >= 7.0]

        return {
            "available": True,
            "n_assets": n_assets,
            "n_scored": n_scored,
            "avg_risk_score": round(avg_risk, 2),
            "n_control_gaps": n_gaps,
            "n_high_risk_assets": len(high_risk),
            "asset_inventory_present": n_assets > 0,
            "risk_scoring_active": n_scored > 0,
            "control_gaps_identified": n_gaps > 0,
            # Used to suggest maturity scores for specific subcategories
            "suggested_scores": {
                "ID.AM-02": 3 if n_assets > 0 else 1,
                "ID.RA-01": 3 if n_scored > 0 else 1,
                "ID.RA-05": 4 if n_scored > 0 and avg_risk > 0 else 2,
                "GV.RM-06": 3 if n_scored > 0 else 1,
            },
        }
