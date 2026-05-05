"""Results dashboard renderer — one function per agent tab."""

from __future__ import annotations

from typing import Any

import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from config import AGENT_META, BUFFETT_CHECKLIST
from ui.components import (
    badge,
    buffett_quote,
    buffett_score_gauge,
    empty_block,
    margin_of_safety_gauge,
    verdict_banner,
)
from utils.formatting import (
    fmt_money,
    fmt_pct,
    fmt_price,
    grade_color,
    sentiment_color,
    truncate,
    verdict_color,
)


# ---------------------------------------------------------------------------
# Top-level dashboard
# ---------------------------------------------------------------------------
def render_dashboard(state: dict) -> None:
    _render_top_summary(state)

    tab_specs: list[tuple[str, str, callable]] = []

    available = {
        "thesis": ("🎯 Thesis", _thesis),
        "business": ("🏢 Business", _business),
        "financials": ("💰 Financials", _financials),
        "moat": ("🛡️ Moat", _moat),
        "management": ("👔 Management", _management),
        "valuation": ("🧮 Valuation", _valuation),
        "sentiment": ("📰 Sentiment", _sentiment),
        "macro": ("🌍 Macro", _macro),
    }
    for key, (label, fn) in available.items():
        if state.get(key):
            tab_specs.append((label, key, fn))

    if state.get("thesis"):
        tab_specs.append(("📋 Buffett Checklist", "_checklist", _checklist))

    if not tab_specs:
        empty_block("No agent results to show yet. Run an analysis to populate this dashboard.")
        return

    tab_labels = [t[0] for t in tab_specs]
    tabs = st.tabs(tab_labels)
    for tab, (_label, key, fn) in zip(tabs, tab_specs):
        with tab:
            fn(state)

    if state.get("errors"):
        st.divider()
        with st.expander(f"⚠️ {len(state['errors'])} agent(s) reported errors"):
            for err in state["errors"]:
                st.error(f"**{err.get('node', '?')}**: {err.get('error', 'unknown')}")


# ---------------------------------------------------------------------------
# Top summary block (always visible)
# ---------------------------------------------------------------------------
def _render_top_summary(state: dict) -> None:
    thesis = state.get("thesis") or {}
    valuation = state.get("valuation") or {}
    business = state.get("business") or {}

    verdict = thesis.get("verdict", "PENDING")
    risk_adjusted = thesis.get("risk_adjusted_verdict", "")
    score = thesis.get("buffett_score")
    mos = valuation.get("margin_of_safety_pct")
    price = valuation.get("current_price")
    iv_mid = (valuation.get("intrinsic_value_range") or {}).get("mid")

    summary_line = risk_adjusted or business.get("buffett_assessment", "")[:240]
    verdict_banner(verdict, summary_line)

    g1, g2, g3 = st.columns(3)
    with g1:
        st.plotly_chart(
            buffett_score_gauge(score),
            use_container_width=True,
            key="hdr_score",
        )
    with g2:
        st.plotly_chart(
            margin_of_safety_gauge(mos),
            use_container_width=True,
            key="hdr_mos",
        )
    with g3:
        st.markdown("##### Price vs intrinsic value")
        st.metric("Current price", fmt_price(price))
        st.metric(
            "Intrinsic value (mid)",
            fmt_price(iv_mid),
            delta=fmt_pct((iv_mid - price) / price) if (iv_mid and price) else None,
        )
        ideal = thesis.get("ideal_entry_price")
        if ideal:
            st.metric("Ideal entry price", fmt_price(ideal))


# ---------------------------------------------------------------------------
# Thesis tab
# ---------------------------------------------------------------------------
def _thesis(state: dict) -> None:
    t = state.get("thesis") or {}
    if "error" in t:
        st.error(f"Thesis agent failed: {t['error']}")
        return

    risk_profile = state.get("risk_profile") or {}
    if risk_profile:
        st.caption(
            f"Tailored to: risk tolerance {risk_profile.get('risk_tolerance', '?')}/10 · "
            f"{risk_profile.get('horizon', '?')} · {risk_profile.get('goal', '?')} · "
            f"{risk_profile.get('experience', '?')} · "
            f"Required MoS {risk_profile.get('required_margin_of_safety', 0):.0%}"
        )

    if t.get("thesis_memo"):
        st.markdown("#### Buffett's Memo")
        buffett_quote(t["thesis_memo"])

    cols = st.columns(2)
    with cols[0]:
        st.markdown("#### Top reasons to BUY")
        for r in t.get("top_reasons_to_buy") or []:
            st.markdown(f"- {r}")
    with cols[1]:
        st.markdown("#### Top reasons to AVOID")
        for r in t.get("top_reasons_to_avoid") or []:
            st.markdown(f"- {r}")

    if t.get("key_risks"):
        st.divider()
        st.markdown("#### Key risks")
        for r in t["key_risks"]:
            st.markdown(f"- {r}")

    st.divider()
    c1, c2, c3 = st.columns(3)
    c1.metric("Verdict", t.get("verdict", "—"))
    c2.metric("Buffett Score", f"{t.get('buffett_score', '—')}/100")
    c3.metric("Position size", t.get("position_sizing_suggestion", "—"))


# ---------------------------------------------------------------------------
# Business tab
# ---------------------------------------------------------------------------
def _business(state: dict) -> None:
    b = state.get("business") or {}
    if "error" in b:
        st.error(f"Business agent failed: {b['error']}")
        return

    st.markdown(f"### {b.get('company_name', state.get('ticker', 'Company'))}  ·  `{b.get('ticker', '')}`")
    st.caption(b.get("industry", ""))

    c1, c2, c3 = st.columns(3)
    c1.metric("Franchise vs commodity", "Franchise" if b.get("is_franchise") else "Commodity")
    c2.metric("Circle of competence", f"{b.get('circle_of_competence_score', '—')}/10")
    c3.metric("Industry", b.get("industry", "—"))

    st.divider()
    st.markdown("**Business description**")
    st.write(b.get("business_description", "—"))

    if b.get("buffett_assessment"):
        st.markdown("**Buffett's read**")
        buffett_quote(b["buffett_assessment"])

    segments = b.get("revenue_segments") or []
    if segments:
        st.divider()
        st.markdown("#### Revenue segments")
        rows = [{"Segment": s.get("name", "—"), "% of revenue": s.get("pct_of_revenue", 0) or 0} for s in segments]
        try:
            fig = px.pie(
                rows,
                names="Segment",
                values="% of revenue",
                color_discrete_sequence=px.colors.sequential.Greens_r,
                hole=0.4,
            )
            fig.update_layout(height=320, margin=dict(l=10, r=10, t=20, b=10))
            st.plotly_chart(fig, use_container_width=True, key="biz_pie")
        except Exception:
            st.dataframe(rows, hide_index=True, use_container_width=True)

    risks = b.get("key_risk_factors") or []
    if risks:
        st.divider()
        st.markdown("#### Key risk factors (from 10-K)")
        for r in risks:
            st.markdown(f"- {r}")


# ---------------------------------------------------------------------------
# Financials tab
# ---------------------------------------------------------------------------
def _financials(state: dict) -> None:
    f = state.get("financials") or {}
    if "error" in f:
        st.error(f"Financials agent failed: {f['error']}")
        return

    grade = f.get("buffett_grade", "—")
    score = f.get("financial_strength_score", "—")
    growth = f.get("growth_rates") or {}
    current = f.get("current_metrics") or {}

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        f"<div style='text-align:center;'><div style='font-size:0.85rem;color:#475569;'>Buffett Grade</div>"
        f"<div style='font-size:2rem; font-weight:700; color:{grade_color(grade)};'>{grade}</div></div>",
        unsafe_allow_html=True,
    )
    c2.metric("Financial strength", f"{score}/10")
    c3.metric("ROE (TTM)", fmt_pct(current.get("roe")))
    c4.metric("D/E", _fmt_ratio(current.get("debt_to_equity")))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Revenue 5yr CAGR", fmt_pct(growth.get("revenue_cagr")))
    c6.metric("EPS 5yr CAGR", fmt_pct(growth.get("eps_cagr")))
    c7.metric("FCF 5yr CAGR", fmt_pct(growth.get("fcf_cagr")))
    c8.metric("FCF margin", fmt_pct(current.get("fcf_margin")))

    st.divider()

    metrics = f.get("metrics_5yr") or {}
    years = f.get("years") or list(range(len(metrics.get("revenue") or [])))
    if years and metrics.get("revenue"):
        rev_fig = _line_chart(
            years,
            {"Revenue": metrics.get("revenue") or [], "Net Income": metrics.get("net_income") or []},
            title="Revenue and net income (5yr)",
            in_dollars=True,
        )
        st.plotly_chart(rev_fig, use_container_width=True, key="fin_rev")

        cf_fig = _line_chart(
            years,
            {"Free cash flow": metrics.get("fcf") or [], "Owner earnings": metrics.get("owner_earnings") or []},
            title="Free cash flow vs owner earnings (5yr)",
            in_dollars=True,
        )
        st.plotly_chart(cf_fig, use_container_width=True, key="fin_cf")

        ratio_fig = _line_chart(
            years,
            {"ROE": metrics.get("roe") or [], "ROIC": metrics.get("roic") or []},
            title="ROE & ROIC (5yr)",
            in_dollars=False,
            as_pct=True,
        )
        st.plotly_chart(ratio_fig, use_container_width=True, key="fin_ratios")

    if f.get("red_flags"):
        st.divider()
        st.markdown("#### 🚩 Red flags")
        for r in f["red_flags"]:
            st.markdown(f"- {r}")

    if f.get("buffett_assessment"):
        st.divider()
        st.markdown("**Buffett's read**")
        buffett_quote(f["buffett_assessment"])


def _line_chart(years: list, series_map: dict[str, list], title: str, in_dollars: bool, as_pct: bool = False) -> go.Figure:
    fig = go.Figure()
    for name, vals in series_map.items():
        if not vals:
            continue
        clean = [v for v in vals if v is not None]
        if not clean:
            continue
        if as_pct:
            display_vals = [v * 100 if v is not None else None for v in vals]
        else:
            display_vals = vals
        fig.add_trace(
            go.Scatter(
                x=years,
                y=display_vals,
                mode="lines+markers",
                name=name,
                line=dict(width=3),
            )
        )
    fig.update_layout(
        title=title,
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", y=-0.2),
        yaxis_tickformat=".1%" if as_pct else None,
    )
    return fig


def _fmt_ratio(v: Any) -> str:
    if v is None:
        return "—"
    try:
        return f"{float(v):.2f}"
    except (TypeError, ValueError):
        return "—"


# ---------------------------------------------------------------------------
# Moat tab
# ---------------------------------------------------------------------------
def _moat(state: dict) -> None:
    m = state.get("moat") or {}
    if "error" in m:
        st.error(f"Moat agent failed: {m['error']}")
        return

    composite = m.get("composite_moat_score")
    trajectory = m.get("moat_trajectory", "—")
    primary = m.get("primary_moat_source", "—")

    c1, c2, c3 = st.columns(3)
    c1.metric("Composite moat", f"{composite}/10" if composite is not None else "—")
    c2.metric("Trajectory", trajectory)
    c3.metric("Primary moat source", primary)

    scores = m.get("moat_scores") or {}
    if scores:
        st.divider()
        labels = ["Brand", "Switching costs", "Network effects", "Cost advantage", "Intangibles"]
        keys = ["brand", "switching_costs", "network_effects", "cost_advantage", "intangibles"]
        values = [float(scores.get(k, 0) or 0) for k in keys]
        fig = go.Figure(
            go.Scatterpolar(
                r=values + [values[0]],
                theta=labels + [labels[0]],
                fill="toself",
                line=dict(color="#10b981", width=3),
                fillcolor="rgba(16,185,129,0.25)",
            )
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(range=[0, 10], visible=True, gridcolor="#e2e8f0")),
            showlegend=False,
            height=380,
            margin=dict(l=20, r=20, t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True, key="moat_radar")

    if m.get("evidence"):
        st.markdown("#### Evidence")
        for e in m["evidence"]:
            st.markdown(f"- {e}")

    if m.get("buffett_assessment"):
        st.divider()
        st.markdown("**Buffett's read**")
        buffett_quote(m["buffett_assessment"])


# ---------------------------------------------------------------------------
# Management tab
# ---------------------------------------------------------------------------
def _management(state: dict) -> None:
    mg = state.get("management") or {}
    if "error" in mg:
        st.error(f"Management agent failed: {mg['error']}")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CEO", mg.get("ceo_name", "—"))
    c2.metric("CEO tenure", f"{mg.get('ceo_tenure_years', '—')} yrs")
    c3.metric("Insider ownership", fmt_pct((mg.get("insider_ownership_pct") or 0) / 100) if mg.get("insider_ownership_pct") and mg["insider_ownership_pct"] > 1 else fmt_pct(mg.get("insider_ownership_pct")))
    c4.metric("Overall score", f"{mg.get('overall_management_score', '—')}/10")

    sub_scores = {
        "Capital allocation": mg.get("capital_allocation_score"),
        "Candor": mg.get("candor_score"),
        "Compensation alignment": mg.get("compensation_alignment_score"),
    }
    chart_rows = [{"Dimension": k, "Score": v or 0} for k, v in sub_scores.items()]
    fig = px.bar(
        chart_rows,
        x="Dimension",
        y="Score",
        color="Dimension",
        color_discrete_sequence=px.colors.sequential.Greens_r,
        range_y=[0, 10],
    )
    fig.update_layout(showlegend=False, height=300, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig, use_container_width=True, key="mgmt_bar")

    if mg.get("recent_capital_decisions"):
        st.markdown("#### Recent capital allocation decisions")
        for d in mg["recent_capital_decisions"]:
            st.markdown(f"- {d}")

    if mg.get("red_flags"):
        st.markdown("#### 🚩 Red flags")
        for r in mg["red_flags"]:
            st.markdown(f"- {r}")

    if mg.get("buffett_assessment"):
        st.divider()
        st.markdown("**Buffett's read**")
        buffett_quote(mg["buffett_assessment"])


# ---------------------------------------------------------------------------
# Valuation tab
# ---------------------------------------------------------------------------
def _valuation(state: dict) -> None:
    v = state.get("valuation") or {}
    if "error" in v:
        st.error(f"Valuation agent failed: {v['error']}")
        return

    price = v.get("current_price")
    iv_range = v.get("intrinsic_value_range") or {}
    valuations = v.get("valuations") or {}

    c1, c2, c3 = st.columns(3)
    c1.metric("Current price", fmt_price(price))
    c2.metric("Intrinsic value (mid)", fmt_price(iv_range.get("mid")))
    c3.metric("Margin of safety", fmt_pct(v.get("margin_of_safety_pct")))

    c4, c5, c6 = st.columns(3)
    c4.metric("DCF value", fmt_price(valuations.get("dcf_value")))
    c5.metric("Owner earnings × 15", fmt_price(valuations.get("owner_earnings_value")))
    c6.metric("EPV", fmt_price(valuations.get("epv_value")))

    c7, c8, c9 = st.columns(3)
    c7.metric("P/E (TTM)", _fmt_ratio(v.get("current_pe")))
    c8.metric("P/FCF", _fmt_ratio(v.get("current_pfcf")))
    c9.metric("Dividend yield", fmt_pct(v.get("dividend_yield")) if v.get("dividend_yield") and v.get("dividend_yield") < 1 else fmt_pct((v.get("dividend_yield") or 0) / 100))

    st.divider()
    st.markdown("#### Intrinsic value range")
    chart_rows = []
    for label, val in [("DCF", valuations.get("dcf_value")), ("Owner earnings", valuations.get("owner_earnings_value")), ("EPV", valuations.get("epv_value"))]:
        if val is not None:
            chart_rows.append({"Method": label, "Per-share value": float(val)})
    if price:
        chart_rows.append({"Method": "Market price", "Per-share value": float(price)})
    if chart_rows:
        fig = px.bar(
            chart_rows,
            x="Method",
            y="Per-share value",
            color="Method",
            color_discrete_map={
                "DCF": "#047857",
                "Owner earnings": "#10b981",
                "EPV": "#34d399",
                "Market price": "#0f172a",
            },
        )
        fig.update_layout(showlegend=False, height=320, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, use_container_width=True, key="val_bar")

    verdict = v.get("valuation_verdict", "—")
    st.markdown(badge(verdict, color=verdict_color(verdict)), unsafe_allow_html=True)

    if v.get("buffett_assessment"):
        st.divider()
        st.markdown("**Buffett's read**")
        buffett_quote(v["buffett_assessment"])

    if v.get("key_assumptions"):
        st.divider()
        st.markdown("#### Key assumptions")
        for a in v["key_assumptions"]:
            st.markdown(f"- {a}")


# ---------------------------------------------------------------------------
# Sentiment tab
# ---------------------------------------------------------------------------
def _sentiment(state: dict) -> None:
    s = state.get("sentiment") or {}
    if "error" in s:
        st.error(f"Sentiment agent failed: {s['error']}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Sentiment", s.get("sentiment_classification", "—"))
    c2.metric("Analyst consensus", s.get("analyst_consensus", "—"))
    c3.metric("Score", f"{s.get('sentiment_score', 0):+.2f}" if s.get("sentiment_score") is not None else "—")

    classification = s.get("sentiment_classification", "")
    color = sentiment_color(classification)
    if "overly bearish" in classification.lower():
        st.markdown(badge("Contrarian opportunity?", color=color), unsafe_allow_html=True)
    elif "overly bullish" in classification.lower():
        st.markdown(badge("⚠️ Crowd is greedy", color=color), unsafe_allow_html=True)

    items = s.get("recent_news") or []
    if items:
        st.divider()
        for item in items:
            url = item.get("url", "")
            headline = item.get("headline", "—")
            link = f'<a href="{url}" target="_blank">{headline}</a>' if url else headline
            sig = item.get("significance", "low")
            sig_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#10b981"}.get(sig.lower(), "#6b7280")
            sent = item.get("sentiment", "neutral")
            sent_color = {"positive": "#10b981", "negative": "#ef4444", "neutral": "#6b7280"}.get(sent.lower(), "#6b7280")
            st.markdown(
                f"""
                <div class="ciq-news-item">
                    <div class="ciq-news-date">{item.get('date', '—')} · {item.get('source', '—')} {badge(sig.upper(), color=sig_color)} {badge(sent.upper(), color=sent_color)}</div>
                    <div class="ciq-news-headline">{link}</div>
                    <div class="ciq-news-summary">{truncate(item.get('headline', ''), 280)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if s.get("key_catalysts"):
        st.divider()
        st.markdown("#### Catalysts to watch")
        for c in s["key_catalysts"]:
            st.markdown(f"- {c}")

    if s.get("buffett_assessment"):
        st.divider()
        st.markdown("**Buffett's read**")
        buffett_quote(s["buffett_assessment"])


# ---------------------------------------------------------------------------
# Macro tab
# ---------------------------------------------------------------------------
def _macro(state: dict) -> None:
    m = state.get("macro") or {}
    if "error" in m:
        st.error(f"Macro agent failed: {m['error']}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Industry outlook", m.get("industry_outlook", "—"))
    c2.metric("Growth rate", m.get("industry_growth_rate", "—"))
    c3.metric("Position", m.get("competitive_position", "—"))

    competitors = m.get("top_competitors") or []
    if competitors:
        st.divider()
        st.markdown("#### Top competitors")
        cols = st.columns(min(3, len(competitors)))
        for col, comp in zip(cols * (len(competitors) // len(cols) + 1), competitors):
            with col:
                level = (comp.get("threat_level") or "").lower()
                threat_color = {"low": "#10b981", "medium": "#f59e0b", "high": "#ef4444"}.get(level, "#6b7280")
                st.markdown(
                    f"""
                    <div class="ciq-card">
                        <h4>{comp.get('name', '—')}</h4>
                        <div class="ciq-sub">Threat level</div>
                        {badge(level.upper() or 'UNKNOWN', color=threat_color)}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    cA, cB = st.columns(2)
    with cA:
        st.markdown("#### Tailwinds")
        for t in m.get("macro_tailwinds") or []:
            st.markdown(f"- {t}")
    with cB:
        st.markdown("#### Headwinds")
        for h in m.get("macro_headwinds") or []:
            st.markdown(f"- {h}")

    if m.get("regulatory_risks"):
        st.divider()
        st.markdown("#### Regulatory risks")
        for r in m["regulatory_risks"]:
            st.markdown(f"- {r}")

    if m.get("buffett_assessment"):
        st.divider()
        st.markdown("**Buffett's read**")
        buffett_quote(m["buffett_assessment"])


# ---------------------------------------------------------------------------
# Buffett checklist tab
# ---------------------------------------------------------------------------
def _checklist(state: dict) -> None:
    thesis = state.get("thesis") or {}
    results = thesis.get("checklist_results") or []

    by_id = {r.get("id"): r for r in results if isinstance(r, dict)}

    pass_color = {"PASS": "#10b981", "FAIL": "#ef4444", "NEUTRAL": "#6b7280"}

    pass_count = sum(1 for r in results if (r.get("result") or "").upper() == "PASS")
    fail_count = sum(1 for r in results if (r.get("result") or "").upper() == "FAIL")

    c1, c2, c3 = st.columns(3)
    c1.metric("Items passed", pass_count)
    c2.metric("Items failed", fail_count)
    c3.metric("Total", len(BUFFETT_CHECKLIST))

    st.divider()
    for item in BUFFETT_CHECKLIST:
        r = by_id.get(item["id"]) or {}
        result = (r.get("result") or "NEUTRAL").upper()
        comment = r.get("comment", "")
        color = pass_color.get(result, "#6b7280")
        weight = item.get("weight", 1)

        st.markdown(
            f"""
            <div class="ciq-check-row">
                <div>{badge(result, color=color)}</div>
                <div class="ciq-q"><b>{item['question']}</b></div>
                <div class="ciq-c">{comment}</div>
                <div style="color:#94a3b8; font-size:0.75rem;">weight {weight}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Single-agent renderer (for Skill Lab)
# ---------------------------------------------------------------------------
SINGLE_AGENT_RENDERERS = {
    "business": _business,
    "financials": _financials,
    "moat": _moat,
    "management": _management,
    "valuation": _valuation,
    "sentiment": _sentiment,
    "macro": _macro,
    "thesis": _thesis,
}


def render_single_agent(agent_id: str, state: dict) -> None:
    meta = AGENT_META.get(agent_id, {"label": agent_id, "emoji": "🤖"})
    st.markdown(f"### {meta['emoji']} {meta['label']}")
    if meta.get("principle"):
        st.caption(f'_"{meta["principle"]}" — Warren Buffett_')
    fn = SINGLE_AGENT_RENDERERS.get(agent_id)
    if fn:
        fn(state)
    else:
        st.json(state.get(agent_id) or {})
