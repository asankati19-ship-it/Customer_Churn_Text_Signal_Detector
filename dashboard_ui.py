"""Shared presentation for upload results and saved customer records."""

import pandas as pd
import streamlit as st

RISK_LEVELS = ["High", "Medium", "Low"]
RISK_COLORS = ["#c24146", "#956010", "#218567"]


def apply_styles():
    st.markdown("""
    <style>
    .stMainBlockContainer {max-width: 1200px; padding-top: 3rem; padding-bottom: 3rem;}
    h1 {letter-spacing: -0.025em;}
    h2, h3 {letter-spacing: -0.015em;}
    [data-testid="stMarkdownContainer"] p {line-height: 1.65;}
    [data-baseweb="tab-list"] {gap: 1.5rem; margin-bottom: 1.5rem;}
    [data-baseweb="tab"] {min-height: 3rem;}
    [data-baseweb="tab"] p {font-size: 1rem; font-weight: 600;}
    [data-testid="stMetric"] {padding: 1rem; border: 1px solid #8884; border-radius: 10px;}
    @media (max-width: 640px) {
      .stMainBlockContainer {padding: 1.5rem 1rem;}
      [data-baseweb="tab-list"] {gap: 0.5rem;}
      [data-baseweb="tab"] p {font-size: 0.875rem;}
    }
    </style>
    """, unsafe_allow_html=True)


def risk_distribution(report):
    counts = report["risk_level"].value_counts().reindex(RISK_LEVELS, fill_value=0)
    data = pd.DataFrame({"Risk": RISK_LEVELS, "Customers": counts.to_numpy()})
    total = int(counts.sum())
    data["Share"] = data["Customers"] / total if total else 0.0
    return data


def show_risk_charts(report, scope):
    data = risk_distribution(report)
    total = int(data["Customers"].sum())
    if not total:
        st.info("Analyze customer messages to see the risk charts.")
        return
    st.subheader("Risk overview")
    st.caption(f"{scope} · {total:,} customer records · Share of analyzed records, not a churn probability.")
    color = {"field": "Risk", "type": "nominal", "sort": RISK_LEVELS,
             "scale": {"domain": RISK_LEVELS, "range": RISK_COLORS},
             "legend": {"title": None, "orient": "bottom", "labelFontSize": 13}}
    tooltip = [{"field": "Risk", "type": "nominal"},
               {"field": "Customers", "type": "quantitative", "format": ",d"},
               {"field": "Share", "type": "quantitative", "format": ".1%"}]
    common = {"height": 280, "config": {"view": {"stroke": None},
              "axis": {"labelFontSize": 13, "titleFontSize": 13}}}
    pie_column, bar_column = st.columns(2, gap="large")
    with pie_column:
        st.markdown("#### Share by risk level")
        st.vega_lite_chart(data, {
            **common, "mark": {"type": "arc", "innerRadius": 65, "outerRadius": 110},
            "encoding": {"theta": {"field": "Customers", "type": "quantitative"},
                         "color": color, "tooltip": tooltip,
                         "order": {"field": "Risk", "sort": "ascending"}},
        }, width="stretch", alt="Donut chart of the share of customer records in each risk category.")
    with bar_column:
        st.markdown("#### Customer counts by risk")
        st.vega_lite_chart(data, {
            **common,
            "encoding": {"x": {"field": "Risk", "type": "nominal", "sort": RISK_LEVELS,
                                "axis": {"title": None, "labelAngle": 0}},
                         "y": {"field": "Customers", "type": "quantitative",
                                "scale": {"zero": True, "domainMax": int(data.Customers.max()) * 1.2},
                                "axis": {"tickMinStep": 1, "format": "d"}},
                         "tooltip": tooltip},
            "layer": [
                {"mark": {"type": "bar", "size": 48, "cornerRadiusTopLeft": 4,
                          "cornerRadiusTopRight": 4},
                 "encoding": {"color": {**color, "legend": None}}},
                {"transform": [{"filter": "datum.Customers > 0"}],
                 "mark": {"type": "text", "dy": 8, "baseline": "top",
                          "fontSize": 14, "fontWeight": "bold", "color": "white"},
                 "encoding": {"text": {"field": "Customers", "type": "quantitative"}}},
            ],
        }, width="stretch", alt="Bar chart comparing customer counts for High, Medium, and Low risk.")
    # Exact values remain available without relying on color or hover.
    st.caption(" · ".join(
        f"{row.Risk}: {row.Customers:,} ({row.Share:.1%})"
        for row in data.itertuples(index=False)
    ))
