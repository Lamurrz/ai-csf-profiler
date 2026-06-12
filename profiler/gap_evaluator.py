"""
profiler/gap_evaluator.py
-------------------------
Compares a Current Profile against a Target Profile and generates
a prioritized remediation roadmap sorted by gap severity × asset risk.
"""

from __future__ import annotations

from typing import Any


PRIORITY_WEIGHTS = {
    "high":   1.5,
    "medium": 1.0,
    "low":    0.5,
}


class GapEvaluator:
    """
    Evaluates gaps between Current and Target profiles and generates
    a prioritized remediation roadmap.
    """

    def evaluate(self, profile: dict[str, Any]) -> dict[str, Any]:
        """
        Evaluate gaps in a profile dict (as returned by ProfileBuilder.build()).
        Returns an evaluation report dict.
        """
        scores = profile.get("scores", {})
        meridian = profile.get("meridian_integration", {})
        avg_risk = meridian.get("avg_risk_score", 0.0)

        gaps = []
        by_function: dict[str, list] = {}
        total_gap = 0
        total_possible = 0

        for sub_id, sub in scores.items():
            current = sub.get("current_maturity", 0)
            target = sub.get("target_maturity", 3)
            gap = sub.get("gap", 0)
            ai_rel = sub.get("ai_relevance", "medium")
            fn = sub.get("function", "Unknown")

            if current == 0:  # skipped
                continue

            total_gap += gap
            total_possible += target

            if gap > 0:
                # Priority score: gap × AI relevance weight × risk boost
                ai_weight = PRIORITY_WEIGHTS.get(ai_rel, 1.0)
                risk_boost = 1.0 + (avg_risk / 10.0)
                priority_score = gap * ai_weight * risk_boost

                gap_entry = {
                    "subcategory_id": sub_id,
                    "function": fn,
                    "title": sub.get("title", ""),
                    "current_maturity": current,
                    "target_maturity": target,
                    "gap": gap,
                    "ai_relevance": ai_rel,
                    "priority_score": round(priority_score, 3),
                    "informative_references": sub.get("informative_references", {}),
                    "notes": sub.get("notes", ""),
                    "remediation_steps": self._remediation_steps(sub_id, gap, ai_rel),
                }
                gaps.append(gap_entry)

            if fn not in by_function:
                by_function[fn] = {"assessed": 0, "gaps": 0, "total_gap": 0,
                                    "avg_current": 0.0, "scores": []}
            by_function[fn]["assessed"] += 1
            by_function[fn]["scores"].append(current)
            if gap > 0:
                by_function[fn]["gaps"] += 1
                by_function[fn]["total_gap"] += gap

        # Sort gaps by priority score descending
        gaps.sort(key=lambda g: g["priority_score"], reverse=True)

        # Compute per-function averages
        for fn_data in by_function.values():
            if fn_data["scores"]:
                fn_data["avg_current"] = round(
                    sum(fn_data["scores"]) / len(fn_data["scores"]), 2
                )

        # Overall maturity score
        assessed = [s for s in scores.values() if s.get("current_maturity", 0) > 0]
        overall_current = (
            sum(s["current_maturity"] for s in assessed) / len(assessed)
            if assessed else 0
        )
        overall_target = profile.get("target_maturity", 3)
        maturity_pct = (overall_current / overall_target * 100) if overall_target else 0

        return {
            "profile_id": profile.get("profile_id", ""),
            "organization": profile.get("organization", ""),
            "evaluated_at": profile.get("created_at", ""),
            "csf_version": "2.0",
            "summary": {
                "overall_current_maturity": round(overall_current, 2),
                "overall_target_maturity": overall_target,
                "maturity_percentage": round(maturity_pct, 1),
                "total_subcategories": len(assessed),
                "subcategories_with_gaps": len(gaps),
                "subcategories_meeting_target": len(assessed) - len(gaps),
                "total_gap_points": total_gap,
            },
            "by_function": by_function,
            "gaps": gaps,
            "meridian_context": {
                "available": meridian.get("available", False),
                "avg_risk_score": avg_risk,
                "n_control_gaps": meridian.get("n_control_gaps", 0),
                "n_high_risk_assets": meridian.get("n_high_risk_assets", 0),
            },
            "top_priorities": gaps[:5],
        }

    def _remediation_steps(self, sub_id: str, gap: int, ai_relevance: str) -> list[str]:
        """Generate remediation guidance per subcategory."""
        steps_map = {
            "GV.OC-01": [
                "Document how AI system deployments align with organizational mission",
                "Conduct AI risk appetite workshop with leadership",
                "Map AI use cases to strategic objectives",
            ],
            "GV.RM-01": [
                "Define AI-specific risk tolerance thresholds (false positive rates, drift limits)",
                "Establish AI risk register with executive sign-off",
                "Implement quarterly AI risk review cadence",
            ],
            "GV.RM-06": [
                "Adopt a standardized AI risk scoring methodology (e.g., Meridian parallel failure model)",
                "Implement automated risk scoring for all AI assets",
                "Document scoring methodology and calibrate annually",
            ],
            "GV.PO-01": [
                "Draft AI security policy covering full ML lifecycle",
                "Define autonomous AI decision-making boundaries",
                "Establish human oversight requirements for high-risk AI decisions",
            ],
            "GV.RR-01": [
                "Designate AI Risk Owner at executive level",
                "Define Model Risk Officer role and responsibilities",
                "Establish AI ethics review board with security representation",
            ],
            "ID.AM-02": [
                "Inventory all AI models, APIs, pipelines, and registries",
                "Classify AI assets by sensitivity and criticality",
                "Integrate AI asset inventory with CMDB",
            ],
            "ID.AM-07": [
                "Catalog all training datasets with provenance and PII classification",
                "Implement data lineage tracking for model inputs",
                "Document synthetic data and third-party dataset usage",
            ],
            "ID.RA-01": [
                "Conduct AI-specific vulnerability assessments (adversarial robustness, prompt injection)",
                "Subscribe to ML framework CVE feeds",
                "Integrate MITRE ATLAS threat intelligence into vulnerability management",
            ],
            "ID.RA-02": [
                "Onboard MITRE ATLAS as primary AI threat intelligence source",
                "Join AI-focused ISAC or threat sharing community",
                "Deploy Meridian knowledge graph for cross-referenced threat intelligence",
            ],
            "ID.RA-05": [
                "Implement quantitative AI risk scoring (Meridian or equivalent)",
                "Conduct attack path analysis for high-criticality AI assets",
                "Integrate risk scores into prioritization decisions",
            ],
            "PR.AA-01": [
                "Inventory all AI service accounts and API keys",
                "Implement API key rotation for LLM service credentials",
                "Enforce MFA for model registry access",
            ],
            "PR.AA-05": [
                "Apply least-privilege to training data and model weight access",
                "Implement rate limiting on all inference APIs",
                "Conduct quarterly access reviews for AI assets",
            ],
            "PR.DS-01": [
                "Encrypt model weights and training data at rest",
                "Implement integrity verification for stored training data",
                "Apply key management controls for AI data encryption",
            ],
            "PR.DS-02": [
                "Enforce TLS for all inference API traffic",
                "Encrypt prompt content and model responses in transit",
                "Implement certificate pinning for high-sensitivity AI endpoints",
            ],
            "PR.PS-01": [
                "Version-control AI infrastructure configuration",
                "Implement configuration drift detection for model serving",
                "Define and enforce baseline configurations for AI containers",
            ],
            "PR.IR-01": [
                "Network-segment AI inference endpoints behind API gateway",
                "Isolate training clusters from production networks",
                "Implement access logging for model registry",
            ],
        }

        steps = steps_map.get(sub_id, [
            f"Assess current state and document gaps for {sub_id}",
            "Develop remediation plan with milestones",
            "Assign ownership and target completion date",
        ])

        # If gap is large (3+), add urgency note
        if gap >= 3:
            steps = [f"[PRIORITY] {steps[0]}"] + steps[1:]

        return steps[:3]  # return top 3 steps
