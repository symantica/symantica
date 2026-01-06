from __future__ import annotations

from dash import Dash, dcc, html
from dash.dependencies import Input, Output

from core.compiler.load import load_project
from core.runtime import MockProvider, QueryContext


def kpi_card(title: str, value: str) -> html.Div:
    return html.Div(
        [
            html.Div(title, style={"fontSize": "12px", "opacity": 0.7}),
            html.Div(value, style={"fontSize": "28px", "fontWeight": "600"}),
        ],
        style={
            "border": "1px solid #eee",
            "borderRadius": "12px",
            "padding": "14px",
            "minWidth": "220px",
        },
    )


def build_app(project_path: str = "examples/underwriting/project.yaml") -> Dash:
    project = load_project(project_path)
    metric_map = {m.name: m for m in project.metrics}

    provider = MockProvider()
    ctx = QueryContext(days=45, breakdown_limit=20)

    app = Dash(__name__)
    app.title = "Symantica (Dash)"

    page_options = [{"label": p.name, "value": p.name} for p in project.dashboard.pages]
    default_page = project.dashboard.pages[0].name if project.dashboard.pages else None

    app.layout = html.Div(
        style={
            "fontFamily": "system-ui, -apple-system, Segoe UI, Roboto, Arial",
            "padding": "18px",
            "maxWidth": "1200px",
            "margin": "0 auto",
            "overflowX": "hidden",
        },
        children=[
            html.H2("Symantica — Dashboard Preview (Dash, Mock Provider)"),
            html.Div(
                style={"display": "flex", "gap": "12px", "alignItems": "center", "marginBottom": "12px"},
                children=[
                    html.Div("Page:", style={"fontWeight": "600"}),
                    dcc.Dropdown(
                        id="page",
                        options=page_options,
                        value=default_page,
                        clearable=False,
                        style={"width": "320px"},
                    ),
                    html.Div("Mode:", style={"fontWeight": "600", "marginLeft": "16px"}),
                    dcc.Dropdown(
                        id="mode",
                        options=[{"label": "Mock", "value": "mock"}],
                        value="mock",
                        clearable=False,
                        style={"width": "200px"},
                    ),
                ],
            ),
            html.Div(id="page_title", style={"fontSize": "18px", "fontWeight": "700", "margin": "10px 0 12px"}),
            html.Div(id="kpis", style={"display": "flex", "gap": "12px", "flexWrap": "wrap", "marginBottom": "16px"}),
            html.Div(
                style={"display": "grid", "gridTemplateColumns": "1.2fr 0.8fr", "gap": "14px", "maxWidth": "100%"},
                children=[
                    html.Div(
                        style={"border": "1px solid #eee", "borderRadius": "12px", "padding": "12px"},
                        children=[
                            html.Div("Trend", style={"fontWeight": "700", "marginBottom": "8px"}),
                            dcc.Graph(
                                id="trend",
                                config={"displayModeBar": False, "responsive": True},
                                style={"width": "100%", "height": "320px"},
                            ),
                        ],
                    ),
                    html.Div(
                        style={"border": "1px solid #eee", "borderRadius": "12px", "padding": "12px"},
                        children=[
                            html.Div("Breakdown", style={"fontWeight": "700", "marginBottom": "8px"}),
                            dcc.Graph(
                                id="breakdown",
                                config={"displayModeBar": False, "responsive": True},
                                style={"width": "100%", "height": "320px"},
                            ),
                        ],
                    ),
                ],
            ),
            html.Div(
                style={"marginTop": "14px", "opacity": 0.7, "fontSize": "12px"},
                children=["Tip: Both Dash and Streamlit use the same DataProvider interface."],
            ),
        ],
    )

    @app.callback(
        Output("page_title", "children"),
        Output("kpis", "children"),
        Output("trend", "figure"),
        Output("breakdown", "figure"),
        Input("page", "value"),
        Input("mode", "value"),
    )
    def render_page(page_name: str, mode: str):
        page = next((p for p in project.dashboard.pages if p.name == page_name), None)
        if not page:
            return "Unknown page", [], {}, {}

        # KPI cards
        cards = []
        for metric_name in page.include_metrics:
            m = metric_map.get(metric_name)
            if not m:
                continue
            label = m.description or m.name
            v = provider.kpi(project, metric_name, ctx)
            value = f"{v*100:.2f}%" if m.format == "percent" else f"{v:,.0f}"
            cards.append(kpi_card(label, value))

        # Trend
        tdf = provider.trend(project, page.include_metrics[0] if page.include_metrics else "metric", ctx)
        trend_fig = {
            "data": [{"x": tdf["date"], "y": tdf["value"], "type": "scatter", "mode": "lines"}],
            "layout": {
                "autosize": True,
                "uirevision": "keep",
                "margin": {"l": 30, "r": 10, "t": 10, "b": 30},
                "height": 320,
            },
        }

        # Breakdown
        dim = page.breakdown_dims[0] if page.breakdown_dims else "category"
        bdf = provider.breakdown(project, page.include_metrics[0] if page.include_metrics else "metric", dim, ctx)
        breakdown_fig = {
            "data": [{"x": bdf["dim"], "y": bdf["value"], "type": "bar"}],
            "layout": {
                "autosize": True,
                "uirevision": "keep",
                "margin": {"l": 30, "r": 10, "t": 10, "b": 80},
                "height": 320,
            },
        }

        return page.name, cards, trend_fig, breakdown_fig

    return app


if __name__ == "__main__":
    app = build_app("examples/underwriting/project.yaml")
    app.run(debug=True, port=8050)
