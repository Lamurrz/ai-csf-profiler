"""
profiler/meridian_client.py
---------------------------
Pulls live data from the Meridian Risk Scoring API and CyberGraph-AD
to auto-populate CSF 2.0 subcategory evidence.
"""

from __future__ import annotations
import logging
from typing import Any

import httpx
from config import settings

logger = logging.getLogger("csf_profiler.meridian")


class MeridianClient:
    def __init__(self, base_url: str = None, cybergraph_url: str = None):
        self._base = (base_url or settings.meridian_api_url).rstrip("/")
        self._cybergraph = (cybergraph_url or getattr(settings, 'cybergraph_api_url', None))
        self._timeout = settings.meridian_timeout

    def _get(self, url: str) -> Any:
        try:
            r = httpx.get(url, timeout=self._timeout)
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            logger.warning(f"API unavailable at {url} ({exc})")
            return None

    def is_available(self) -> bool:
        result = self._get(f"{self._base}/health")
        return result is not None and result.get("neo4j_connected", False)

    def get_assets(self) -> list[dict]:
        return self._get(f"{self._base}/assets") or []

    def get_control_gaps(self) -> dict:
        return self._get(f"{self._base}/controls/gaps") or {"total_gaps": 0, "gaps": []}

    def get_cybergraph_summary(self) -> dict:
        """Pull anomaly detection summary from CyberGraph-AD if available."""
        if not self._cybergraph:
            return {}
        result = self._get(f"{self._cybergraph}/summary")
        return result or {}

    def summarize_for_csf(self) -> dict[str, Any]:
        """
        Summarize Meridian + CyberGraph-AD data into CSF-relevant evidence.
        """
        if not self.is_available():
            return {"available": False}

        assets = self.get_assets()
        gaps = self.get_control_gaps()
        cybergraph = self.get_cybergraph_summary()

        n_assets = len(assets)
        n_scored = sum(1 for a in assets if a.get("risk_score") is not None)
        avg_risk = (
            sum(a["risk_score"] for a in assets if a.get("risk_score"))
            / max(n_scored, 1)
        )
        n_gaps = gaps.get("total_gaps", 0)
        high_risk = [a for a in assets if (a.get("risk_score") or 0) >= 7.0]

        # CyberGraph-AD evidence for Detect subcategories
        anomalies_detected = cybergraph.get("anomalies_detected", 0)
        findings_emitted = cybergraph.get("findings_emitted", 0)
        detection_active = anomalies_detected > 0 or findings_emitted > 0

        # Suggest maturity scores based on evidence
        suggested = {
            # Identify
            "ID.AM-02": 3 if n_assets > 0 else 1,
            "ID.RA-01": 3 if n_scored > 0 else 1,
            "ID.RA-05": 4 if n_scored > 0 and avg_risk > 0 else 2,
            "GV.RM-06": 3 if n_scored > 0 else 1,
            # Detect — CyberGraph-AD evidence
            "DE.CM-01": 3 if detection_active else 1,
            "DE.CM-03": 3 if detection_active else 1,
            "DE.AE-02": 3 if detection_active and n_scored > 0 else 1,
            "DE.AE-06": 3 if findings_emitted > 0 else 1,
        }

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
            "cybergraph_detection_active": detection_active,
            "anomalies_detected": anomalies_detected,
            "findings_emitted": findings_emitted,
            "suggested_scores": suggested,
        }
