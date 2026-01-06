from __future__ import annotations

from datetime import date, timedelta

import streamlit as st

from core.compiler.load import load_project
from core.runtime import MockProvider, QueryContext


def main():
    st.set_page_config(page_title="Symantica", layout="wide")
    st.title("Symantica — Dashboard Preview (Mock Provider)")

    project_path = st.text_input("Project YAML path", value="examples/underwriting/project.yaml")
    project = load_project(project_path)

    st.sidebar.header("Data Source")
    mode = st.sidebar.radio("Mode", options=["Mock"], index=0)

    # Filters (not applied yet; reserved for BigQuery provider later)
    st.sidebar.header("Filters (UI only for now)")
    _ = st.sidebar.date_input("Date range", value=(date.today() - timedelta(days=30), date.today()))
    _ = st.sidebar.selectbox("Channel", options=["All", "Paid", "Organic", "Partner"])
    _ = st.sidebar.selectbox("State", options=["All", "CA", "TX", "NY"])

    ctx = QueryContext(days=45, breakdown_limit=20)
    provider = MockProvider()

    metric_map = {m.name: m for m in project.metrics}

    for page in project.dashboard.pages:
        st.header(page.name)

        # KPIs
        cols = st.columns(min(4, max(1, len(page.include_metrics))))
        for i, metric_name in enumerate(page.include_metrics):
            m = metric_map.get(metric_name)
            if not m:
                continue

            label = m.description or m.name
            v = provider.kpi(project, metric_name, ctx)

            if m.format == "percent":
                cols[i % len(cols)].metric(label=label, value=f"{v*100:.2f}%")
            else:
                cols[i % len(cols)].metric(label=label, value=f"{v:,.0f}")

        # Trend (first metric on page)
        if page.include_metrics:
            st.subheader("Trend")
            df = provider.trend(project, page.include_metrics[0], ctx)
            st.line_chart(df.set_index("date"))

        # Breakdown (first dim only, MVP)
        if page.breakdown_dims and page.include_metrics:
            dim = page.breakdown_dims[0]
            st.subheader(f"Breakdown by {dim}")
            df = provider.breakdown(project, page.include_metrics[0], dim, ctx)
            st.dataframe(df, use_container_width=True)


if __name__ == "__main__":
    main()
