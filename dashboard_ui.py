"""Shared presentation for upload results and saved customer records."""

import pandas as pd
import streamlit as st

RISK_LEVELS = ["High", "Medium", "Low"]
RISK_COLORS = ["#c24146", "#956010", "#218567"]


def show_records(records, key):
    search, filters = st.columns([3, 2], gap="large")
    with search:
        query = st.text_input("Search customer ID or name", placeholder="Find a customer…", key=f"{key}_search").strip()
    with filters:
        levels = st.multiselect("Risk filter", RISK_LEVELS, default=RISK_LEVELS, key=f"{key}_risk")
    filtered = records[records.risk_level.isin(levels)]
    if query:
        filtered = filtered[filtered.customer_id.str.contains(query, case=False, regex=False, na=False)
                            | filtered.customer_name.str.contains(query, case=False, regex=False, na=False)]
    st.caption(f"Showing {len(filtered)} of {len(records)} saved customers. Overview totals above include all customers.")
    columns = ["customer_id", "customer_name", "risk_level", "sentiment", "sentiment_score",
               "retention_action", "recent_message", "matched_signals", "risk_score", "analyzed_at"]
    st.dataframe(filtered[columns], width="stretch", hide_index=True,
                 column_config={**{c: st.column_config.TextColumn(c.replace('_', ' ').title())
                                for c in columns if c not in ("sentiment_score", "risk_score")},
                                "customer_id": st.column_config.TextColumn("Customer ID"),
                                "sentiment_score": st.column_config.NumberColumn("Sentiment score", format="%.2f"),
                                "risk_score": st.column_config.NumberColumn("Risk score", format="%d")})
    if not filtered.empty:
        selected = st.selectbox("Read full customer record", filtered.customer_id.tolist(), key=f"{key}_detail")
        row = filtered[filtered.customer_id == selected].iloc[0]
        with st.expander("Full message and recommended action"):
            st.caption("CUSTOMER MESSAGE")
            st.write(row.recent_message)
            st.caption("RECOMMENDED NEXT STEP")
            st.info(row.retention_action)
    st.download_button("Download filtered records", filtered.to_csv(index=False).encode("utf-8"),
                       "filtered_customers.csv", "text/csv", key=f"{key}_download")


def apply_styles():
    st.markdown("""
    <style>
    .stApp {background: #f5f7fb; color: #18253b;}
    .stMainBlockContainer {max-width: 1280px; padding-top: 2.5rem; padding-bottom: 3rem;}
    h1 {letter-spacing: -0.045em; font-weight: 750;}
    h2, h3 {letter-spacing: -0.025em; color: #18253b;}
    [data-testid="stHeader"] {background: #f5f7fb;}
    [data-testid="stSidebar"] {background: #11243a; border-right: 0;}
    [data-testid="stSidebar"] * {color: #e4edf7;}
    [data-testid="stSidebar"] h1 {font-size: 1.5rem;}
    [data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {color: #b9cadd;}
    .brand-mark {display:inline-flex; width:42px; height:42px; align-items:center; justify-content:center; border-radius:12px; background:#14b8a6; color:#092c32; font-size:24px; font-weight:800; margin-bottom:20px;}
    .hero {background:#11243a; border-radius:22px; padding:36px 40px; margin-bottom:26px; color:#fff; position:relative; overflow:hidden;}
    .hero .eyebrow {font-size:11px; letter-spacing:2px; font-weight:700; color:#78dfd0; margin:0 0 14px;}
    .hero h1 {color:#fff; font-size:38px; line-height:1.15; margin:0 0 14px; padding:0; max-width:720px;}
    .hero p {font-size:15px; color:#c4d3e3; max-width:650px; margin:0; line-height:1.7;}
    .hero .tag {display:inline-block; margin-top:24px; font-size:11px; border:1px solid #52667b; border-radius:30px; padding:6px 12px; color:#d7e6f2;}
    .side-section {font-size:10px; letter-spacing:2px; color:#8ba4bd; margin-top:30px; margin-bottom:12px;}
    .side-step {padding:12px 0; border-bottom:1px solid #314458; font-size:13px; line-height:1.7;}
    .side-step span {color:#90a8bf; display:block; font-size:12px;}
    [data-testid="stMarkdownContainer"] p {line-height: 1.65;}
    [role="tablist"] {gap: .5rem; margin-bottom: 1.5rem; background:#e9eef5; padding:6px; border-radius:13px;}
    [role="tab"] {min-height: 3rem; border-radius:9px; padding:0 22px; color:#52647a;}
    [role="tab"][aria-selected="true"] {background:#fff; color:#0c766d; box-shadow:0 2px 5px #18253b12;}
    [data-baseweb="tab-highlight"], [data-baseweb="tab-border"] {display:none;}
    [role="tab"] p {font-size: 1rem; font-weight: 600;}
    [data-testid="stMetric"] {padding: 22px; border: 1px solid #e0e7ef; border-top:3px solid #159b8b; border-radius: 14px; background:#fff; box-shadow:0 4px 16px #18253b04;}
    [data-testid="stMetricValue"] {font-weight:750; letter-spacing:-1px;}
    [data-testid="stMetricLabel"] {color:#64748b;}
    [data-testid="stVerticalBlockBorderWrapper"] > div {border-color:#e0e7ef !important; border-radius:16px !important;}
    [data-testid="stDataFrame"], [data-testid="stExpander"] {border-radius:12px; overflow:hidden; background:#fff;}
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {background:#fff; color:#18253b;}
    [data-testid="stButton"] button, [data-testid="stDownloadButton"] button {border-radius:9px; font-weight:600; min-height:42px;}
    [data-testid="stButton"] button[kind="primary"] {background:#087f73; border-color:#087f73; color:#fff;}
    [data-testid="stButton"] button[kind="primary"]:hover {background:#06685f;}
    button:focus-visible, input:focus-visible, textarea:focus-visible {outline:3px solid #52b8ab !important; outline-offset:3px;}
    [data-testid="stVegaLiteChart"] {background:#fff; border:1px solid #e0e7ef; border-radius:14px; padding:12px;}
    hr {border-color:#e0e7ef;}
    @media (max-width: 640px) {
      .stMainBlockContainer {padding: 1.5rem 1rem;}
      .hero {padding:26px 22px; border-radius:16px;}
      .hero h1 {font-size:29px;}
      [role="tab"] {padding:0 10px;}
      [role="tablist"] {gap: 0.5rem;}
      [role="tab"] p {font-size: 0.875rem;}
    }
    </style>
    """, unsafe_allow_html=True)


def show_header():
    st.markdown('''<section class="hero">
    <div class="eyebrow">CUSTOMER INTELLIGENCE / RETENTION WORKSPACE</div>
    <h1>Understand the signal.<br>Make the next move.</h1>
    <p>Turn customer messages into clear retention priorities. Spot concerns,
    understand intent, and give every conversation a thoughtful next step.</p>
    <span class="tag">Text analysis</span> <span class="tag">Explainable signals</span>
    <span class="tag">CRM ready</span></section>''', unsafe_allow_html=True)


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
    common = {"height": 280, "padding": {"top": 24, "bottom": 24, "left": 24, "right": 24}, "config": {"view": {"stroke": None},
              "axis": {"labelFontSize": 13, "titleFontSize": 13}}}
    pie_column, bar_column = st.columns(2, gap="large")
    with pie_column:
        st.markdown("#### Share by risk level")
        st.vega_lite_chart(data, {
            **common, "mark": {"type": "arc", "innerRadius": 65, "outerRadius": 90},
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



