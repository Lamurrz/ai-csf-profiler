"""
run.py
------
AI CSF Profiler CLI entry point.

Usage
-----
# Interactive profile assessment
python run.py --mode assess

# Generate gap report from existing profile
python run.py --mode report --profile output/csf-profile-*.json

# Full pipeline: assess + report
python run.py --mode full

# Demo mode (no interaction, uses auto-populated scores)
python run.py --mode demo
"""

import argparse
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("csf_profiler")


def mode_assess(args):
    from profiler.profile_builder import ProfileBuilder
    builder = ProfileBuilder(output_dir=args.output_dir)
    profile = builder.build(
        org_name=args.org,
        target_maturity=args.target,
        auto_meridian=not args.no_meridian,
        interactive=True,
    )
    print(f"\nProfile ID: {profile['profile_id']}")
    print(f"Subcategories assessed: {len(profile['scores'])}")
    return profile


def mode_report(args):
    from profiler.gap_evaluator import GapEvaluator
    from report.json_reporter import JSONReporter
    from report.pdf_reporter import PDFReporter

    # Find profile file
    if args.profile:
        profile_path = Path(args.profile)
    else:
        profiles = sorted(Path(args.output_dir).glob("csf-profile-*.json"))
        if not profiles:
            print("No profile found. Run --mode assess first.")
            sys.exit(1)
        profile_path = profiles[-1]  # most recent

    with open(profile_path) as f:
        profile = json.load(f)

    logger.info(f"Evaluating profile: {profile_path}")

    evaluator = GapEvaluator()
    evaluation = evaluator.evaluate(profile)

    # JSON report
    json_reporter = JSONReporter(output_dir=args.output_dir)
    json_path = json_reporter.save(evaluation)
    logger.info(f"JSON report saved → {json_path}")

    # PDF report
    pdf_reporter = PDFReporter(output_dir=args.output_dir)
    pdf_path = pdf_reporter.save(evaluation)
    logger.info(f"PDF report saved → {pdf_path}")

    # Print summary
    summary = evaluation["summary"]
    print(f"\n{'='*50}")
    print(f"  CSF 2.0 Gap Report — {evaluation['organization']}")
    print(f"{'='*50}")
    print(f"  Overall maturity:  {summary['overall_current_maturity']:.1f} / {summary['overall_target_maturity']}.0  ({summary['maturity_percentage']:.0f}%)")
    print(f"  Subcategories:     {summary['total_subcategories']} assessed, {summary['subcategories_with_gaps']} with gaps")
    print(f"\n  Top 3 priorities:")
    for i, g in enumerate(evaluation["top_priorities"][:3], 1):
        print(f"    {i}. {g['subcategory_id']} — gap: {g['gap']} levels (priority: {g['priority_score']:.2f})")
    print(f"\n  JSON → {json_path}")
    print(f"  PDF  → {pdf_path}")

    return evaluation


def mode_full(args):
    profile = mode_assess(args)

    # Save profile path for report
    profile_path = Path(args.output_dir) / f"{profile['profile_id']}.json"
    args.profile = str(profile_path)
    mode_report(args)


def mode_demo(args):
    """Non-interactive demo mode — auto-populates scores for testing."""
    from profiler.profile_builder import ProfileBuilder
    from profiler.gap_evaluator import GapEvaluator
    from report.json_reporter import JSONReporter
    from report.pdf_reporter import PDFReporter

    logger.info("Running in demo mode (non-interactive)")

    builder = ProfileBuilder(output_dir=args.output_dir)
    profile = builder.build(
        org_name=args.org or "Demo Organization",
        target_maturity=args.target,
        auto_meridian=not args.no_meridian,
        interactive=False,
    )

    evaluator = GapEvaluator()
    evaluation = evaluator.evaluate(profile)

    json_reporter = JSONReporter(output_dir=args.output_dir)
    json_path = json_reporter.save(evaluation)

    pdf_reporter = PDFReporter(output_dir=args.output_dir)
    pdf_path = pdf_reporter.save(evaluation)

    summary = evaluation["summary"]
    logger.info(f"Demo complete — maturity: {summary['overall_current_maturity']:.1f}/{summary['overall_target_maturity']}, "
                f"gaps: {summary['subcategories_with_gaps']}")
    logger.info(f"JSON → {json_path}")
    logger.info(f"PDF  → {pdf_path}")

    return evaluation


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI CSF Profiler — NIST CSF 2.0 Gap Evaluator")
    parser.add_argument("--mode", default="demo",
                        choices=["assess", "report", "full", "demo"])
    parser.add_argument("--org", default=None, help="Organization name")
    parser.add_argument("--target", type=int, default=3,
                        help="Target maturity level (1-5, default: 3)")
    parser.add_argument("--profile", default=None,
                        help="Path to existing profile JSON (for --mode report)")
    parser.add_argument("--output-dir", default="output",
                        help="Output directory for reports")
    parser.add_argument("--no-meridian", action="store_true",
                        help="Skip Meridian Risk API integration")

    args = parser.parse_args()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)

    modes = {
        "assess":    mode_assess,
        "report":    mode_report,
        "full":      mode_full,
        "demo":      mode_demo,
    }
    modes[args.mode](args)
