"""
report/pdf_reporter.py
----------------------
Generates a formatted PDF gap report using ReportLab.

Sections
--------
1. Executive Summary — overall maturity, top gaps, Meridian context
2. Per-Function Maturity — Govern, Identify, Protect breakdown
3. Gap Analysis Table — all gaps sorted by priority
4. Remediation Roadmap — top 10 prioritized actions
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak,
)


# ── Color palette ─────────────────────────────────────────────────────────────
DARK_BLUE  = colors.HexColor("#0C447C")
MED_BLUE   = colors.HexColor("#1D6FA8")
LIGHT_BLUE = colors.HexColor("#E6F1FB")
TEAL       = colors.HexColor("#1D9E75")
LIGHT_TEAL = colors.HexColor("#E1F5EE")
AMBER      = colors.HexColor("#E8A020")
CORAL      = colors.HexColor("#C84B20")
GRAY       = colors.HexColor("#6B7280")
LIGHT_GRAY = colors.HexColor("#F3F4F6")
WHITE      = colors.white
BLACK      = colors.black

FUNCTION_COLORS = {
    "Govern":   DARK_BLUE,
    "Identify": TEAL,
    "Protect":  MED_BLUE,
}

MATURITY_COLORS = {
    1: CORAL,
    2: AMBER,
    3: colors.HexColor("#2563EB"),
    4: TEAL,
    5: colors.HexColor("#065F46"),
}


def _maturity_bar(score: int, target: int, width: int = 50) -> str:
    filled = int((score / 5) * width)
    return "█" * filled + "░" * (width - filled) + f"  {score}/{target}"


class PDFReporter:
    def __init__(self, output_dir: str = "output"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, evaluation: dict[str, Any], filename: str = None) -> str:
        if not filename:
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            org = evaluation.get("organization", "org").replace(" ", "_")
            filename = f"csf_gap_report_{org}_{ts}.pdf"

        path = self._output_dir / filename
        self._build(evaluation, str(path))
        return str(path)

    def _build(self, ev: dict[str, Any], path: str) -> None:
        doc = SimpleDocTemplate(
            path,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        story = []

        # ── Custom styles ─────────────────────────────────────────────────────
        h1 = ParagraphStyle("H1", parent=styles["Heading1"],
                            fontSize=20, textColor=DARK_BLUE, spaceAfter=6)
        h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                            fontSize=14, textColor=DARK_BLUE, spaceAfter=4,
                            spaceBefore=12)
        h3 = ParagraphStyle("H3", parent=styles["Heading3"],
                            fontSize=11, textColor=MED_BLUE, spaceAfter=3,
                            spaceBefore=8)
        body = ParagraphStyle("Body", parent=styles["Normal"],
                              fontSize=9, leading=13, spaceAfter=4)
        small = ParagraphStyle("Small", parent=styles["Normal"],
                               fontSize=8, textColor=GRAY, leading=11)
        caption = ParagraphStyle("Caption", parent=styles["Normal"],
                                 fontSize=8, textColor=GRAY, alignment=TA_CENTER)

        summary = ev.get("summary", {})
        org = ev.get("organization", "Organization")
        meridian = ev.get("meridian_context", {})

        # ── Cover ─────────────────────────────────────────────────────────────
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph("AI Security CSF 2.0 Gap Report", h1))
        story.append(Paragraph(org, ParagraphStyle("Org", parent=h2,
                                                    fontSize=16, textColor=GRAY)))
        story.append(Paragraph(
            f"Generated: {datetime.now(timezone.utc).strftime('%B %d, %Y')} | "
            f"CSF Version: 2.0 | Functions: Govern · Identify · Protect",
            small,
        ))
        story.append(HRFlowable(width="100%", thickness=2, color=DARK_BLUE,
                                spaceAfter=12))

        # ── Executive Summary ─────────────────────────────────────────────────
        story.append(Paragraph("Executive Summary", h2))

        current = summary.get("overall_current_maturity", 0)
        target = summary.get("overall_target_maturity", 3)
        pct = summary.get("maturity_percentage", 0)
        n_gaps = summary.get("subcategories_with_gaps", 0)
        n_assessed = summary.get("total_subcategories", 0)
        n_meeting = summary.get("subcategories_meeting_target", 0)

        # Summary table
        summary_data = [
            ["Metric", "Value"],
            ["Overall Current Maturity", f"{current:.1f} / {target}.0"],
            ["Maturity Achievement", f"{pct:.0f}%"],
            ["Subcategories Assessed", str(n_assessed)],
            ["Meeting Target", f"{n_meeting} ({100*n_meeting//max(n_assessed,1)}%)"],
            ["Gaps Identified", str(n_gaps)],
        ]
        if meridian.get("available"):
            summary_data += [
                ["Meridian Avg Risk Score", f"{meridian.get('avg_risk_score', 0):.1f} / 10"],
                ["Control Gaps (Meridian)", str(meridian.get("n_control_gaps", 0))],
                ["High-Risk Assets", str(meridian.get("n_high_risk_assets", 0))],
            ]

        summary_table = Table(summary_data, colWidths=[3 * inch, 3 * inch])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, GRAY),
            ("ALIGN", (1, 0), (1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 12))

        # ── Per-function breakdown ─────────────────────────────────────────────
        story.append(Paragraph("Maturity by Function", h2))
        by_fn = ev.get("by_function", {})

        fn_data = [["Function", "Assessed", "Gaps", "Avg Current", "Status"]]
        for fn_name, fn_info in by_fn.items():
            avg = fn_info.get("avg_current", 0)
            status = "✓ On Target" if avg >= target else f"↑ Gap: {target - avg:.1f}"
            fn_data.append([
                fn_name,
                str(fn_info.get("assessed", 0)),
                str(fn_info.get("gaps", 0)),
                f"{avg:.1f}",
                status,
            ])

        fn_table = Table(fn_data, colWidths=[1.8*inch, 1*inch, 0.8*inch, 1.2*inch, 2.2*inch])
        fn_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("GRID", (0, 0), (-1, -1), 0.5, GRAY),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(fn_table)
        story.append(Spacer(1, 12))

        # ── Gap analysis table ─────────────────────────────────────────────────
        story.append(PageBreak())
        story.append(Paragraph("Gap Analysis", h2))
        story.append(Paragraph(
            "Subcategories where current maturity falls below target, "
            "sorted by priority score (gap × AI relevance × risk).", body
        ))
        story.append(Spacer(1, 6))

        gaps = ev.get("gaps", [])
        if gaps:
            gap_data = [["ID", "Function", "Current", "Target", "Gap", "AI Rel.", "Priority"]]
            for g in gaps:
                gap_data.append([
                    g["subcategory_id"],
                    g["function"],
                    str(g["current_maturity"]),
                    str(g["target_maturity"]),
                    str(g["gap"]),
                    g["ai_relevance"].title(),
                    f"{g['priority_score']:.2f}",
                ])
            gap_table = Table(gap_data,
                              colWidths=[0.9*inch, 0.9*inch, 0.65*inch,
                                         0.65*inch, 0.55*inch, 0.75*inch, 0.8*inch])
            gap_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), DARK_BLUE),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_TEAL]),
                ("GRID", (0, 0), (-1, -1), 0.5, GRAY),
                ("ALIGN", (2, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(gap_table)
        else:
            story.append(Paragraph("No gaps identified — all subcategories meet target.", body))

        # ── Remediation roadmap ────────────────────────────────────────────────
        story.append(PageBreak())
        story.append(Paragraph("Remediation Roadmap", h2))
        story.append(Paragraph(
            "Top priority remediation actions, ordered by gap severity × AI relevance × asset risk.",
            body
        ))
        story.append(Spacer(1, 6))

        top = ev.get("top_priorities", gaps[:10])
        for i, g in enumerate(top, 1):
            story.append(Paragraph(
                f"{i}. <b>{g['subcategory_id']}</b> — {g['title'][:80]}",
                ParagraphStyle("RoadmapItem", parent=body,
                               fontSize=9, textColor=DARK_BLUE, spaceBefore=6)
            ))
            story.append(Paragraph(
                f"Gap: {g['gap']} levels | Priority: {g['priority_score']:.2f} | "
                f"AI Relevance: {g['ai_relevance'].title()}",
                small
            ))
            for step in g.get("remediation_steps", []):
                story.append(Paragraph(f"  • {step}", small))
            story.append(Spacer(1, 4))

        # ── Footer note ────────────────────────────────────────────────────────
        story.append(Spacer(1, 0.3 * inch))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GRAY))
        story.append(Paragraph(
            "Generated by AI CSF Profiler | NIST CSF 2.0 | "
            "Informative references: NIST AI RMF, ISO/IEC 42001, MITRE ATLAS, OWASP LLM Top 10",
            caption
        ))

        doc.build(story)
