from dash import get_asset_url, html, register_page
import dash_bootstrap_components as dbc

register_page(__name__, path="/")

layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        [
                            html.Img(src=get_asset_url("india_color2.svg")),
                        ],
                        href="/district-gis",
                    ),
                    width="auto",
                    style={"paddingTop": "20px"},
                ),
            ],
            justify="center",
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        [
                            html.Img(src=get_asset_url("scatter_trend.svg")),
                        ],
                        href="/district-scatter",
                    ),
                    width="auto",
                    style={"paddingTop": "20px"},
                ),
            ],
            justify="center",
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        [
                            html.Img(src=get_asset_url("trend_line.svg")),
                        ],
                        href="/state-trend",
                    ),
                    width="auto",
                    style={"paddingTop": "20px"},
                ),
            ],
            justify="center",
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.A(
                        [
                            html.Img(src=get_asset_url("trend_bar_color2.svg")),
                        ],
                        href="/state-equity",
                    ),
                    width="auto",
                    style={"paddingTop": "20px"},
                ),
            ],
            justify="center",
            align="center",
        ),
        html.Br(),
    ],
    fluid=True,
)
