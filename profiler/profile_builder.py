"""
profiler/profile_builder.py
---------------------------
CLI walkthrough that guides a user through assessing maturity for each
CSF 2.0 subcategory and saves the resulting Current Profile as JSON.

Maturity scale (CMMI-aligned)
------------------------------
1 = Initial     — ad hoc, undocumented
2 = Developing  — some processes defined but inconsistently applied
3 = Defined     — documented, standardized, consistently applied
4 = Managed     — measured, monitored, with quantitative targets
5 = Optimizing  — continuously improved, proactive
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from profiler.meridian_client import MeridianClient

MATURITY_LABELS = {
    1: "Initial — ad hoc, undocumented",
    2: "Developing — defined but inconsistently applied",
    3: "Defined — documented and consistently applied",
    4: "Managed — measured with quantitative targets",
    5: "Optimizing — continuously improved",
}

FUNCTION_COLORS = {
    "GV": "\033[95m",  # magenta
    "ID": "\033[94m",  # blue
    "PR": "\033[92m",  # green
}
RESET = "\033[0m"
BOLD = "\033[1m"


def _load_subcategories(data_path: str = "data/csf_subcategories.json") -> list[dict]:
    with open(data_path) as f:
        return json.load(f)


def _print_header():
    print(f"\n{BOLD}{'='*60}")
    print("  AI CSF Profiler — NIST CSF 2.0 Current Profile Builder")
    print(f"{'='*60}{RESET}\n")
    print("This tool walks you through assessing your organization's")
    print("current maturity for CSF 2.0 subcategories relevant to AI systems.")
    print("\nMaturity scale:")
    for level, label in MATURITY_LABELS.items():
        print(f"  {BOLD}{level}{RESET} = {label}")
    print()


def _print_subcategory(sub: dict, idx: int, total: int, meridian_hint: int | None):
    fn_id = sub["function_id"]
    color = FUNCTION_COLORS.get(fn_id, "")
    print(f"\n{color}{BOLD}[{idx}/{total}] {sub['id']} — {sub['function']} › {sub['category']}{RESET}")
    print(f"{BOLD}{sub['title']}{RESET}")
    print(f"\n{sub['description']}")

    if sub.get("ai_notes"):
        print(f"\n{BOLD}AI context:{RESET} {sub['ai_notes']}")

    refs = sub.get("informative_references", {})
    ref_parts = []
    if refs.get("nist_ai_rmf"):
        ref_parts.append(f"NIST AI RMF: {', '.join(refs['nist_ai_rmf'])}")
    if refs.get("iso_42001"):
        ref_parts.append(f"ISO/IEC 42001: {', '.join(refs['iso_42001'])}")
    if refs.get("mitre_atlas"):
        ref_parts.append(f"MITRE ATLAS: {', '.join(refs['mitre_atlas'])}")
    if refs.get("owasp_llm"):
        ref_parts.append(f"OWASP LLM: {', '.join(refs['owasp_llm'])}")
    if ref_parts:
        print(f"\n{BOLD}References:{RESET} {' | '.join(ref_parts)}")

    if meridian_hint:
        print(f"\n{BOLD}Meridian suggestion:{RESET} {meridian_hint} "
              f"({MATURITY_LABELS[meridian_hint].split('—')[0].strip()}) "
              f"— based on live asset and risk data")


def _get_maturity_input(sub_id: str, hint: int | None) -> tuple[int, str]:
    """Prompt for maturity score and optional notes. Returns (score, notes)."""
    while True:
        prompt = f"\nCurrent maturity for {sub_id} [1-5"
        if hint:
            prompt += f", Enter={hint}"
        prompt += "]: "
        raw = input(prompt).strip()

        if raw == "" and hint:
            score = hint
        elif raw in ("1", "2", "3", "4", "5"):
            score = int(raw)
        elif raw.lower() in ("s", "skip"):
            return 0, ""
        else:
            print("  Please enter 1-5, or 's' to skip.")
            continue

        notes = input(f"  Notes (optional, Enter to skip): ").strip()
        return score, notes


class ProfileBuilder:
    def __init__(
        self,
        data_path: str = "data/csf_subcategories.json",
        output_dir: str = "output",
    ):
        self._subcategories = _load_subcategories(data_path)
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._meridian = MeridianClient()

    def build(
        self,
        org_name: str = None,
        target_maturity: int = 3,
        auto_meridian: bool = True,
        interactive: bool = True,
    ) -> dict[str, Any]:
        """
        Run the profile builder. Returns the completed profile dict.

        Parameters
        ----------
        org_name : str — Organization name for the report header
        target_maturity : int — Default target maturity (1-5)
        auto_meridian : bool — Whether to pull Meridian suggestions
        interactive : bool — If False, uses target_maturity for all scores (for testing)
        """
        if interactive:
            _print_header()

        # Pull Meridian data
        meridian_data = {}
        if auto_meridian:
            print("Connecting to Meridian Risk API...")
            meridian_data = self._meridian.summarize_for_csf()
            if meridian_data.get("available"):
                print(f"  Connected — {meridian_data['n_assets']} assets, "
                      f"{meridian_data['n_control_gaps']} control gaps\n")
            else:
                print("  Meridian API not available — proceeding without integration\n")

        if not org_name and interactive:
            org_name = input("Organization name: ").strip() or "My Organization"

        scores: dict[str, dict] = {}
        total = len(self._subcategories)

        for idx, sub in enumerate(self._subcategories, 1):
            hint = meridian_data.get("suggested_scores", {}).get(sub["id"])

            if interactive:
                _print_subcategory(sub, idx, total, hint)
                score, notes = _get_maturity_input(sub["id"], hint)
            else:
                 # Simulate realistic mixed maturity for demo
                # High AI relevance subcategories tend to score lower (more work needed)
                if sub.get("ai_relevance") == "high":
                    score = hint or max(1, target_maturity - 1)
                else:
                    score = hint or target_maturity
                notes = "Auto-populated"

            scores[sub["id"]] = {
                "subcategory_id": sub["id"],
                "function": sub["function"],
                "category": sub["category"],
                "title": sub["title"],
                "current_maturity": score,
                "target_maturity": target_maturity,
                "gap": max(0, target_maturity - score),
                "notes": notes,
                "meridian_suggested": hint,
                "ai_relevance": sub.get("ai_relevance", "medium"),
                "informative_references": sub.get("informative_references", {}),
            }

        profile = {
            "profile_id": f"csf-profile-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}",
            "organization": org_name or "My Organization",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "csf_version": "2.0",
            "functions_assessed": ["Govern", "Identify", "Protect"],
            "target_maturity": target_maturity,
            "meridian_integration": meridian_data,
            "scores": scores,
        }

        # Save profile
        path = self._output_dir / f"{profile['profile_id']}.json"
        with open(path, "w") as f:
            json.dump(profile, f, indent=2)

        if interactive:
            print(f"\n{BOLD}Profile saved → {path}{RESET}")

        return profile
