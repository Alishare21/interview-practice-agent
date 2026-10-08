"""Create a polished PDF review from one interview session and coach notes."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (KeepTogether, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src import interview_log


NAVY = colors.HexColor("#16324F")
TEAL = colors.HexColor("#147D80")
PALE = colors.HexColor("#EEF4F7")
GRID = colors.HexColor("#D9E4EA")
TEXT = colors.HexColor("#243447")
MUTED = colors.HexColor("#64748B")
STATUS_COLORS = {
    "correct": colors.HexColor("#236B4A"),
    "partly_correct": colors.HexColor("#A35B00"),
    "incorrect": colors.HexColor("#A23B3B"),
    "skipped": colors.HexColor("#64748B"),
    "abandoned": colors.HexColor("#64748B"),
}


def _styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="ReportTitle", parent=styles["Title"],
                              fontName="Helvetica-Bold", fontSize=24, leading=29,
                              textColor=NAVY, alignment=TA_LEFT, spaceAfter=7))
    styles.add(ParagraphStyle(name="ReportSubtitle", parent=styles["Normal"],
                              fontSize=10, leading=15, textColor=MUTED, spaceAfter=12))
    styles.add(ParagraphStyle(name="SectionHead", parent=styles["Heading2"],
                              fontName="Helvetica-Bold", fontSize=14, leading=18,
                              textColor=NAVY, spaceBefore=8, spaceAfter=7))
    styles.add(ParagraphStyle(name="QuestionHead", parent=styles["Heading3"],
                              fontName="Helvetica-Bold", fontSize=11, leading=15,
                              textColor=NAVY, spaceBefore=4, spaceAfter=5))
    styles.add(ParagraphStyle(name="ReportBody", parent=styles["BodyText"],
                              fontSize=9, leading=13, textColor=TEXT, spaceAfter=6))
    styles.add(ParagraphStyle(name="ReportSmall", parent=styles["BodyText"],
                              fontSize=7.5, leading=10, textColor=MUTED, spaceAfter=4))
    styles.add(ParagraphStyle(name="TableText", parent=styles["BodyText"],
                              fontSize=7.5, leading=9.5, textColor=TEXT))
    styles.add(ParagraphStyle(name="TableHeader", parent=styles["BodyText"],
                              fontName="Helvetica-Bold", fontSize=7.5, leading=9,
                              textColor=colors.white))
    styles.add(ParagraphStyle(name="BannerText", parent=styles["BodyText"],
                              fontName="Helvetica-Bold", fontSize=8, leading=10,
                              textColor=colors.white))
    return styles


def _p(text, style="ReportBody"):
    from xml.sax.saxutils import escape

    return Paragraph(escape(str(text)).replace("\n", "<br/>"), STYLES[style])


def _meta_cell(value: str, caption: str):
    return Paragraph(f"<b>{value}</b><br/>{caption}", STYLES["ReportBody"])


STYLES = _styles()


def _footer(canvas, doc):
    canvas.saveState()
    width, _ = letter
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(doc.leftMargin, 0.55 * inch, width - doc.rightMargin, 0.55 * inch)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 0.36 * inch, "INTERVIEW PRACTICE  |  PRIVATE LEARNING REPORT")
    canvas.drawRightString(width - doc.rightMargin, 0.36 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _banner(text):
    table = Table([[_p(text.upper(), "BannerText")]], colWidths=[7.0 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY), ("LEFTPADDING", (0, 0), (-1, -1), 9),
        ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _topic_label(topic_id: str) -> str:
    return topic_id.removeprefix("custom:").replace("-", " ").title()


def _assessment(review: dict) -> str:
    if review.get("status") == "skipped":
        return "Skipped"
    if review.get("status") == "abandoned":
        return "Not answered"
    return {"correct": "Correct", "partly_correct": "Partly correct",
            "incorrect": "Needs correction", "strong": "Strong",
            "developing": "Developing", "needs_work": "Needs work"}.get(
                review.get("assessment"), "Scored")


def _question_block(number: int, review: dict, note: dict):
    status = review.get("assessment") or review.get("status") or "skipped"
    color = STATUS_COLORS.get(status, MUTED)
    topic = _topic_label(review.get("topic_id", "Interview topic"))
    score = review.get("overall")
    result = _assessment(review)
    score_text = f"{score:.1f} / 5" if isinstance(score, (int, float)) else "No score"
    elements = [_banner(f"Question {number}  |  {topic}"), Spacer(1, 6),
                _p(review.get("question") or "Question text was not recorded.", "QuestionHead")]
    label = Table([[_p(f"{result}  |  {score_text}")]], colWidths=[7.0 * inch])
    label.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.Color(color.red, color.green, color.blue, alpha=0.10)),
        ("TEXTCOLOR", (0, 0), (-1, -1), color), ("BOX", (0, 0), (-1, -1), .5, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.extend([label, Spacer(1, 6)])
    scores = review.get("scores")
    if isinstance(scores, dict):
        dims = ["relevance", "structure", "depth", "communication", "impact"]
        data = [[_p(x.title(), "TableHeader") for x in dims],
                [str(scores.get(x, "-")) for x in dims]]
        score_table = Table(data, colWidths=[1.4 * inch] * 5)
        score_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), TEAL), ("BACKGROUND", (0, 1), (-1, 1), PALE),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), .35, GRID), ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        elements.extend([score_table, Spacer(1, 6)])
    elements.append(_p("What your answer showed: " + (note.get("what_showed") or review.get("feedback_summary", "No detailed feedback was recorded."))))
    if note.get("why_it_matters"):
        elements.append(_p("Why this matters: " + note["why_it_matters"]))
    if note.get("improved_answer"):
        elements.append(_p("Example of a stronger answer: " + note["improved_answer"]))
    return KeepTogether(elements)


def create_report(session_id: str, analysis: dict | None = None, output: Path | None = None) -> Path:
    summary = interview_log.session_summary(session_id)
    if summary.get("status") == "not_found":
        raise ValueError(f"No interview session found: {session_id}")
    analysis = analysis or {}
    safe_id = re.sub(r"[^A-Za-z0-9._-]+", "-", session_id).strip(".-") or "session"
    output = output or interview_log.ROOT / "output" / "pdf" / f"interview-report-{safe_id}.pdf"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    reviews = summary.get("question_reviews", [])
    notes = analysis.get("reviews", {})
    scored = [r for r in reviews if isinstance(r.get("overall"), (int, float))]
    topics = ", ".join(dict.fromkeys(_topic_label(r.get("topic_id", "")) for r in reviews))
    story = [Spacer(1, .18 * inch), _p("Interview Practice Report", "ReportTitle"),
             _p(f"{topics or 'Interview practice'}  |  Session {session_id}", "ReportSubtitle")]

    meta_data = [[_meta_cell(str(len(reviews)), "Questions asked"),
                  _meta_cell(str(len(scored)), "Scored answers"),
                  _meta_cell(str(summary.get("skipped", 0)), "Skipped"),
                  _meta_cell(f"{summary['average_score']:.2f} / 5" if summary.get("average_score") is not None else "-", "Average")]]
    meta = Table(meta_data, colWidths=[1.75 * inch] * 4)
    meta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), PALE), ("BOX", (0, 0), (-1, -1), .5, GRID),
                              ("INNERGRID", (0, 0), (-1, -1), .5, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                              ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("TOPPADDING", (0, 0), (-1, -1), 9),
                              ("BOTTOMPADDING", (0, 0), (-1, -1), 9)]))
    story += [meta, Spacer(1, 9), _p("Executive summary", "SectionHead"),
              _p(analysis.get("overview", "This report reviews the answers given in this practice session. Scores reflect the answers observed and the fixed practice rubric."))]

    story.append(_p("Results at a glance", "SectionHead"))
    table_rows = [[_p(x, "TableHeader") for x in ["#", "Topic", "Assessment", "Score"]]]
    for index, review in enumerate(reviews, 1):
        table_rows.append([_p(str(index), "TableText"),
                           _p(_topic_label(review.get("topic_id", "")), "TableText"),
                           _p(_assessment(review), "TableText"),
                           _p(f"{review['overall']:.1f}" if isinstance(review.get("overall"), (int, float)) else "-", "TableText")])
    glance = Table(table_rows, colWidths=[.35 * inch, 2.1 * inch, 2.9 * inch, .75 * inch], repeatRows=1)
    glance.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY),
                                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                                ("GRID", (0, 0), (-1, -1), .35, GRID), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                ("ALIGN", (0, 0), (0, -1), "CENTER"), ("ALIGN", (-1, 1), (-1, -1), "CENTER"),
                                ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(glance)

    dims = summary.get("dimension_averages", {})
    if dims:
        story.append(_p("Dimension averages", "SectionHead"))
        names = ["relevance", "structure", "depth", "communication", "impact"]
        data = [[_p(name.title(), "TableHeader") for name in names],
                [f"{dims.get(name, 0):.1f}" for name in names]]
        t = Table(data, colWidths=[1.4 * inch] * 5)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), TEAL), ("BACKGROUND", (0, 1), (-1, 1), PALE),
                               ("ALIGN", (0, 0), (-1, -1), "CENTER"), ("GRID", (0, 0), (-1, -1), .35, GRID),
                               ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story += [Spacer(1, 7), t]
    for label, key in [("Demonstrated knowledge", "demonstrated_knowledge"),
                       ("Strengths", "strengths"), ("Areas to improve", "weak_points")]:
        values = analysis.get(key, [])
        if values:
            story.append(_p(label, "SectionHead"))
            story.append(_p("\n".join(f"- {item}" for item in values)))
    focus = analysis.get("recommended_focus") or summary.get("recommended_focus")
    if focus:
        story += [_p("Recommended next practice", "SectionHead"), _p(focus)]
    story += [Spacer(1, 5), _p("Scoring note: Correct, partly correct, and needs-correction labels follow the relevance rubric score and should be read with the question-specific explanation. They are practice signals, not hiring predictions. Full answers and résumé text are not included in the practice log by default.", "ReportSmall")]

    story.append(_p("Question-by-question review", "SectionHead"))
    for number, review in enumerate(reviews, 1):
        story.append(_question_block(number, review, notes.get(review.get("question_id"), {})))
        story.append(Spacer(1, 12))

    doc = SimpleDocTemplate(str(output), pagesize=letter, rightMargin=.75 * inch,
                            leftMargin=.75 * inch, topMargin=.7 * inch, bottomMargin=.75 * inch,
                            title="Interview Practice Report", author="Interview Practice Coach",
                            subject="Question-by-question interview practice feedback")
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    return output.resolve()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--analysis", type=Path, help="Optional coach-written JSON review notes")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    analysis = json.loads(args.analysis.read_text(encoding="utf-8")) if args.analysis else None
    print(create_report(args.session_id, analysis, args.output))


if __name__ == "__main__":
    main()
