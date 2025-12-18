"""PDF and CSV report generation for a job's ranked candidates."""
from __future__ import annotations

import csv
import io

from sqlalchemy.orm import Session

from app.repositories import candidate_repo, job_repo


def generate_csv(db: Session, job_id: int) -> bytes:
    _, rows = candidate_repo.list_ranked(db, job_id=job_id, page=1, page_size=10000)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Rank", "Name", "Email", "Experience (yrs)", "Overall %", "Skill %",
         "Experience %", "Education %", "Matching Skills", "Missing Skills",
         "Recommendation", "Status"]
    )
    for idx, (cand, score) in enumerate(rows, start=1):
        writer.writerow([
            idx,
            cand.name or "",
            cand.email or "",
            cand.total_experience_years,
            round(score.overall_score, 1),
            round(score.skill_score, 1),
            round(score.experience_score, 1),
            round(score.education_score, 1),
            "; ".join(score.matching_skills or []),
            "; ".join(score.missing_skills or []),
            score.recommendation or "",
            score.status.value,
        ])
    return buffer.getvalue().encode("utf-8")


def generate_pdf(db: Session, job_id: int) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )

    job = job_repo.get(db, job_id)
    _, rows = candidate_repo.list_ranked(db, job_id=job_id, page=1, page_size=200)

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, title=f"Screening Report - {job.title if job else job_id}")
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("AI Resume Screening Report", styles["Title"]))
    if job:
        elements.append(Paragraph(f"Job: {job.title}", styles["Heading2"]))
        elements.append(Paragraph(f"Department: {job.department or 'N/A'} | Location: {job.location or 'N/A'}", styles["Normal"]))
        elements.append(Paragraph(f"Required skills: {', '.join(job.skills or []) or 'N/A'}", styles["Normal"]))
    elements.append(Spacer(1, 8 * mm))

    table_data = [["Rank", "Candidate", "Score", "Exp", "Recommendation"]]
    for idx, (cand, score) in enumerate(rows, start=1):
        table_data.append([
            str(idx),
            (cand.name or "Unknown")[:28],
            f"{score.overall_score:.0f}%",
            f"{cand.total_experience_years:.0f}y",
            (score.recommendation or "")[:40],
        ])

    table = Table(table_data, colWidths=[15 * mm, 50 * mm, 20 * mm, 15 * mm, 60 * mm])
    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f3f4f6")]),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    elements.append(table)

    # Top candidate detail.
    if rows:
        top_cand, top_score = rows[0]
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph("Top Candidate Analysis", styles["Heading2"]))
        elements.append(Paragraph(f"<b>{top_cand.name or 'Unknown'}</b> - {top_score.overall_score:.0f}% match", styles["Normal"]))
        if top_score.summary:
            elements.append(Paragraph(top_score.summary, styles["Normal"]))
        if top_score.strengths:
            elements.append(Paragraph("Strengths: " + "; ".join(top_score.strengths), styles["Normal"]))
        if top_score.missing_skills:
            elements.append(Paragraph("Missing skills: " + ", ".join(top_score.missing_skills), styles["Normal"]))

    doc.build(elements)
    return buffer.getvalue()
