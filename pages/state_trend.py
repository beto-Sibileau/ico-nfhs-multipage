from dash import callback, dcc, html, Input, Output, register_page
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px

from . import nfhs_345_states, nfhs_345_ind_df, df_nfhs_345, label_no_fig

register_page(__name__, path="/state_trend", title="State Trends")

# %%
# dcc dropdown: nfhs 345 states --> dcc allows multi, styling not as dbc
dd_state_4_trend = dcc.Dropdown(
    id="state-trend-dd",
    options=[{"label": l, "value": l} for l in nfhs_345_states],
    value="Kerala",
    multi=True,
    persistence=True,
    persistence_type="session",
)

# initial indicator type
ini_ind_type = "Population and Household Profile"
# dcc dropdown: nfhs 345 indicator type --> dcc allows multi, styling not as dbc
dd_indicator_type = dcc.Dropdown(
    id="indicator-type-dd",
    options=[
        {"label": l, "value": l}
        for l in sorted(nfhs_345_ind_df["Indicator Type"].unique(), key=str.lower)
    ],
    value=ini_ind_type,
    multi=True,
    persistence=True,
    persistence_type="session",
)

# dcc dropdown: nfhs 345 indicators --> dcc allows multi, styling not as dbc
ini_indicators_345 = sorted(
    nfhs_345_ind_df.query("`Indicator Type` == @ini_ind_type").Indicator.values,
    key=str.lower,
)
dd_indicator_345 = dcc.Dropdown(
    id="indicator-345-dd",
    multi=True,
)

# %%
# dbc state trends row
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select India and/or State/s",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_state_4_trend,
                        ],
                        style={"font-size": "75%"},
                    ),
                    width=2,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Indicator Type",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_indicator_type,
                        ],
                        style={"font-size": "85%"},
                    ),
                    width=4,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select KPI",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            html.Div(dd_indicator_345, id="dd_indicator_345_container"),
                        ],
                        style={"font-size": "85%"},
                    ),
                    width=6,
                ),
            ],
            justify="evenly",
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="state-trend-plot", figure=label_no_fig), width=12
                ),
            ],
            justify="evenly",
            align="center",
        ),
    ],
    fluid=True,
    style={"paddingTop": "20px"},
)

# %%
@callback(
    Output("dd_indicator_345_container", "children"),
    Input("indicator-type-dd", "value"),
)
# update dropdown options: indicator 345 based on indicator type/s
def update_indicator_options(indicator_type):

    if not indicator_type:
        return []

    # dcc dropdown: nfhs 345 indicators --> dcc allows multi, styling not as dbc
    indicators_345 = sorted(
        nfhs_345_ind_df.query("`Indicator Type` in @indicator_type").Indicator.values,
        key=str.lower,
    )
    return dcc.Dropdown(
        id="indicator-345-dd",
        options=[{"label": l, "value": l} for l in indicators_345],
        value=indicators_345[0],
        persistence_type="session",
        persistence=indicator_type[0],
        multi=True,
    )


# %%
@callback(
    Output("state-trend-plot", "figure"),
    Input("state-trend-dd", "value"),
    Input("indicator-345-dd", "value"),
)
def update_trend(state_values, kpi_values):

    if not state_values or not kpi_values:
        return label_no_fig

    display_df = (
        df_nfhs_345.query("State in @state_values & Indicator in @kpi_values")
        .melt(
            id_vars=["Indicator", "State", "NFHS", "Year (give as a period)"],
            value_vars=["Urban", "Rural", "Total"],
        )
        .dropna(subset="value")
        .drop_duplicates(
            subset=["State", "Indicator", "Year (give as a period)", "variable"]
        )
        .sort_values(
            ["Year (give as a period)", "State", "Indicator"],
            ignore_index=True,
        )
        .set_index(["State", "Indicator"])
        .astype({"value": "float64"})
    )

    if display_df.empty:
        return label_no_fig
    else:
        trend_fig = px.line(
            display_df,
            x="Year (give as a period)",
            y="value",
            color=list(display_df.index),
            symbol="variable",
            line_dash="variable",
            line_shape="spline",
            render_mode="svg,",
            hover_data=["NFHS"],
        ).update_traces(mode="lines+markers")

        trend_fig.update_layout(legend=dict(font=dict(size=8), y=0.5, x=1.1))

        return trend_fig
