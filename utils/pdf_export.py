"""ReportLab-based PDF export for the full Buffett brief."""

from __future__ import annotations

import io
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from config import BUFFETT_CHECKLIST, DISCLAIMER


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ciq_title",
            parent=base["Title"],
            fontName="Times-Bold",
            fontSize=22,
            textColor=colors.HexColor("#064e3b"),
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "ciq_subtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#475569"),
            spaceAfter=14,
        ),
        "h2": ParagraphStyle(
            "ciq_h2",
            parent=base["Heading2"],
            fontName="Times-Bold",
            fontSize=15,
            textColor=colors.HexColor("#047857"),
            spaceBefore=14,
            spaceAfter=6,
        ),
        "h3": ParagraphStyle(
            "ciq_h3",
            parent=base["Heading3"],
            fontName="Times-Bold",
            fontSize=12,
            textColor=colors.HexColor("#0f172a"),
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "ciq_body",
            parent=base["Normal"],
            fontName="Times-Roman",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            spaceAfter=4,
        ),
        "small": ParagraphStyle(
            "ciq_small",
            parent=base["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=2,
        ),
        "verdict": ParagraphStyle(
            "ciq_verdict",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=20,
            textColor=colors.HexColor("#047857"),
            spaceBefore=10,
            spaceAfter=10,
        ),
        "disclaimer": ParagraphStyle(
            "ciq_disclaimer",
            parent=base["Normal"],
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#78350f"),
            spaceBefore=12,
            spaceAfter=6,
        ),
    }


def _esc(text: Any) -> str:
    if text is None:
        return "—"
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _kv_table(rows: list[list[str]]) -> Table:
    table = Table(rows, colWidths=[1.7 * inch, 4.6 * inch])
    table.setStyle(
        TableStyle(
            [
                ("FONT", (0, 0), (-1, -1), "Times-Roman", 10),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#475569")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#0f172a")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LINEBELOW", (0, 0), (-1, -2), 0.25, colors.HexColor("#d1fae5")),
            ]
        )
    )
    return table


def _fmt_pct(v: Any) -> str:
    try:
        return f"{float(v) * 100:.1f}%"
    except (TypeError, ValueError):
        return "—"


def _fmt_money(v: Any) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "—"
    sign = "-" if f < 0 else ""
    f = abs(f)
    if f >= 1e12:
        return f"{sign}${f / 1e12:.2f}T"
    if f >= 1e9:
        return f"{sign}${f / 1e9:.2f}B"
    if f >= 1e6:
        return f"{sign}${f / 1e6:.2f}M"
    return f"{sign}${f:,.2f}"


def build_pdf(state: dict) -> bytes:
    """Render the Buffett brief and return raw PDF bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=LETTER,
        leftMargin=0.7 * inch,
        rightMargin=0.7 * inch,
        topMargin=0.6 * inch,
        bottomMargin=0.6 * inch,
        title=f"OracleIQ — {state.get('ticker', 'Report')}",
    )
    styles = _styles()
    story: list = []

    ticker = state.get("ticker", "—")
    mode = state.get("mode", "—")
    risk = state.get("risk_profile") or {}

    story.append(Paragraph(f"OracleIQ — {_esc(ticker)}", styles["title"]))
    story.append(
        Paragraph(
            f"Mode: <b>{_esc(mode)}</b> · Risk tolerance: "
            f"<b>{_esc(risk.get('risk_tolerance', '—'))}</b>/10 · "
            f"Required MoS: <b>{_fmt_pct(risk.get('required_margin_of_safety'))}</b>",
            styles["subtitle"],
        )
    )

    # Disclaimer
    story.append(Paragraph(f"<b>Disclaimer.</b> {DISCLAIMER}", styles["disclaimer"]))

    # Verdict
    thesis = state.get("thesis") or {}
    if thesis and "error" not in thesis:
        story.append(Paragraph("Verdict", styles["h2"]))
        story.append(Paragraph(_esc(thesis.get("verdict", "—")), styles["verdict"]))
        if thesis.get("buffett_score") is not None:
            story.append(Paragraph(f"<b>Buffett Score:</b> {thesis['buffett_score']}/100", styles["body"]))
        if thesis.get("risk_adjusted_verdict"):
            story.append(Paragraph(_esc(thesis["risk_adjusted_verdict"]), styles["body"]))
        if thesis.get("ideal_entry_price"):
            story.append(
                Paragraph(
                    f"<b>Ideal entry price:</b> {_fmt_money(thesis['ideal_entry_price'])}",
                    styles["body"],
                )
            )
        if thesis.get("position_sizing_suggestion"):
            story.append(
                Paragraph(
                    f"<b>Position size suggestion:</b> {_esc(thesis['position_sizing_suggestion'])}",
                    styles["body"],
                )
            )

        if thesis.get("thesis_memo"):
            story.append(Paragraph("Buffett's Memo", styles["h3"]))
            story.append(Paragraph(_esc(thesis["thesis_memo"]), styles["body"]))

        if thesis.get("top_reasons_to_buy"):
            story.append(Paragraph("Top reasons to BUY", styles["h3"]))
            for r in thesis["top_reasons_to_buy"]:
                story.append(Paragraph(f"• {_esc(r)}", styles["body"]))

        if thesis.get("top_reasons_to_avoid"):
            story.append(Paragraph("Top reasons to AVOID", styles["h3"]))
            for r in thesis["top_reasons_to_avoid"]:
                story.append(Paragraph(f"• {_esc(r)}", styles["body"]))

    # Business
    business = state.get("business") or {}
    if business and "error" not in business:
        story.append(Paragraph("Business", styles["h2"]))
        rows = [
            ["Industry", business.get("industry", "—")],
            ["Franchise vs commodity", "Franchise" if business.get("is_franchise") else "Commodity"],
            ["Circle of competence", f"{business.get('circle_of_competence_score', '—')}/10"],
        ]
        story.append(_kv_table(rows))
        if business.get("business_description"):
            story.append(Paragraph(_esc(business["business_description"]), styles["body"]))

    # Financials
    fin = state.get("financials") or {}
    if fin and "error" not in fin:
        story.append(Paragraph("Financials", styles["h2"]))
        cur = fin.get("current_metrics") or {}
        gr = fin.get("growth_rates") or {}
        rows = [
            ["Buffett Grade", fin.get("buffett_grade", "—")],
            ["Financial strength", f"{fin.get('financial_strength_score', '—')}/10"],
            ["ROE (TTM)", _fmt_pct(cur.get("roe"))],
            ["ROIC (TTM)", _fmt_pct(cur.get("roic"))],
            ["Debt / Equity", f"{cur.get('debt_to_equity'):.2f}" if cur.get("debt_to_equity") is not None else "—"],
            ["Revenue 5yr CAGR", _fmt_pct(gr.get("revenue_cagr"))],
            ["EPS 5yr CAGR", _fmt_pct(gr.get("eps_cagr"))],
            ["FCF 5yr CAGR", _fmt_pct(gr.get("fcf_cagr"))],
        ]
        story.append(_kv_table(rows))
        if fin.get("buffett_assessment"):
            story.append(Paragraph(_esc(fin["buffett_assessment"]), styles["body"]))

    # Moat
    moat = state.get("moat") or {}
    if moat and "error" not in moat:
        story.append(Paragraph("Moat", styles["h2"]))
        scores = moat.get("moat_scores") or {}
        rows = [
            ["Composite moat score", f"{moat.get('composite_moat_score', '—')}/10"],
            ["Trajectory", moat.get("moat_trajectory", "—")],
            ["Primary source", moat.get("primary_moat_source", "—")],
            ["Brand", f"{scores.get('brand', '—')}/10"],
            ["Switching costs", f"{scores.get('switching_costs', '—')}/10"],
            ["Network effects", f"{scores.get('network_effects', '—')}/10"],
            ["Cost advantage", f"{scores.get('cost_advantage', '—')}/10"],
            ["Intangibles", f"{scores.get('intangibles', '—')}/10"],
        ]
        story.append(_kv_table(rows))
        if moat.get("buffett_assessment"):
            story.append(Paragraph(_esc(moat["buffett_assessment"]), styles["body"]))

    # Management
    mgmt = state.get("management") or {}
    if mgmt and "error" not in mgmt:
        story.append(Paragraph("Management", styles["h2"]))
        rows = [
            ["CEO", mgmt.get("ceo_name", "—")],
            ["Tenure (yrs)", str(mgmt.get("ceo_tenure_years", "—"))],
            ["Insider ownership", f"{mgmt.get('insider_ownership_pct', '—')}%"],
            ["Capital allocation", f"{mgmt.get('capital_allocation_score', '—')}/10"],
            ["Candor", f"{mgmt.get('candor_score', '—')}/10"],
            ["Compensation alignment", f"{mgmt.get('compensation_alignment_score', '—')}/10"],
            ["Overall management score", f"{mgmt.get('overall_management_score', '—')}/10"],
        ]
        story.append(_kv_table(rows))
        if mgmt.get("buffett_assessment"):
            story.append(Paragraph(_esc(mgmt["buffett_assessment"]), styles["body"]))

    # Valuation
    val = state.get("valuation") or {}
    if val and "error" not in val:
        story.append(Paragraph("Valuation", styles["h2"]))
        valuations = val.get("valuations") or {}
        iv = val.get("intrinsic_value_range") or {}
        rows = [
            ["Current price", _fmt_money(val.get("current_price"))],
            ["Intrinsic value (low)", _fmt_money(iv.get("low"))],
            ["Intrinsic value (mid)", _fmt_money(iv.get("mid"))],
            ["Intrinsic value (high)", _fmt_money(iv.get("high"))],
            ["DCF value", _fmt_money(valuations.get("dcf_value"))],
            ["Owner earnings × 15", _fmt_money(valuations.get("owner_earnings_value"))],
            ["EPV", _fmt_money(valuations.get("epv_value"))],
            ["Margin of safety", _fmt_pct(val.get("margin_of_safety_pct"))],
            ["Valuation verdict", val.get("valuation_verdict", "—")],
        ]
        story.append(_kv_table(rows))
        if val.get("buffett_assessment"):
            story.append(Paragraph(_esc(val["buffett_assessment"]), styles["body"]))

    # Sentiment
    sent = state.get("sentiment") or {}
    if sent and "error" not in sent:
        story.append(Paragraph("Sentiment & News", styles["h2"]))
        rows = [
            ["Classification", sent.get("sentiment_classification", "—")],
            ["Analyst consensus", sent.get("analyst_consensus", "—")],
        ]
        story.append(_kv_table(rows))
        for item in sent.get("recent_news") or []:
            story.append(
                Paragraph(
                    f"<b>{_esc(item.get('headline', '—'))}</b>",
                    styles["h3"],
                )
            )
            story.append(
                Paragraph(
                    f"{_esc(item.get('date', '—'))} · {_esc(item.get('source', '—'))} · "
                    f"sig: {_esc(item.get('significance', '—'))}",
                    styles["small"],
                )
            )

    # Macro
    macro = state.get("macro") or {}
    if macro and "error" not in macro:
        story.append(Paragraph("Macro & Industry", styles["h2"]))
        rows = [
            ["Industry outlook", macro.get("industry_outlook", "—")],
            ["Industry growth rate", macro.get("industry_growth_rate", "—")],
            ["Competitive position", macro.get("competitive_position", "—")],
        ]
        story.append(_kv_table(rows))
        for tw in macro.get("macro_tailwinds") or []:
            story.append(Paragraph(f"+ {_esc(tw)}", styles["body"]))
        for hw in macro.get("macro_headwinds") or []:
            story.append(Paragraph(f"− {_esc(hw)}", styles["body"]))

    # Buffett Checklist
    if thesis and thesis.get("checklist_results"):
        story.append(Paragraph("Buffett Checklist", styles["h2"]))
        by_id = {r.get("id"): r for r in thesis["checklist_results"] if isinstance(r, dict)}
        for item in BUFFETT_CHECKLIST:
            r = by_id.get(item["id"]) or {}
            result = (r.get("result") or "NEUTRAL").upper()
            comment = r.get("comment", "")
            story.append(
                Paragraph(
                    f"[{result}] <b>{_esc(item['question'])}</b> — {_esc(comment)}",
                    styles["body"],
                )
            )

    # Errors
    if state.get("errors"):
        story.append(Paragraph("Agents that failed", styles["h2"]))
        for err in state["errors"]:
            story.append(
                Paragraph(
                    f"• <b>{_esc(err.get('node'))}</b>: {_esc(err.get('error'))}",
                    styles["body"],
                )
            )

    # Filings used
    if state.get("sec_filings_used"):
        story.append(Paragraph("SEC filings consulted", styles["h2"]))
        for f in state["sec_filings_used"]:
            story.append(
                Paragraph(
                    f"• <b>{_esc(f.get('form'))}</b> filed {_esc(f.get('filing_date'))} — used by {_esc(f.get('agent'))}",
                    styles["body"],
                )
            )

    story.append(Spacer(1, 18))
    story.append(
        Paragraph(
            f"<b>Disclaimer.</b> {DISCLAIMER}",
            styles["disclaimer"],
        )
    )

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
