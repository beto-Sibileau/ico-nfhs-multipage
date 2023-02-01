import csv
from dash import callback, dcc, html, Input, Output, State, register_page
from dash.dash_table import DataTable, FormatTemplate
import dash_bootstrap_components as dbc
import pandas as pd
from pandas.api.types import CategoricalDtype
import plotly.express as px

from . import df_equity, equity_kpi_type_df, equity_kpi_types, label_no_fig

register_page(__name__, path="/state-equity", title="State Equity")

# %%
# equity regions (Rakesh to omit these below, revert meeting Luigi 14/09/22)
# union_territories = [
#     "Andaman and Nicobar Islands",
#     "Dadra and Nagar Haveli",
#     "Daman and Diu",
#     "Chandigarh",
#     "Lakshadweep",
#     "Puducherry",
#     "Ladakh",
# ]

# names to display in dropdown equity
# states_4_equity = df_equity.State.unique()

dd_states_equity = dbc.Select(
    id="dd-states-equity",
    options=[
        {"label": l, "value": l}
        for l in sorted(df_equity.State.unique(), key=str.lower)
    ],
    value="All India",
    persistence=True,
    persistence_type="session",
)

# %%
# dbc Select one disaggregation
selected_disaggregation = [
    "Wealth",
    "Residence",
    "Women's Education",
    "Caste",
    "Religion",
]
dd_equity_disagg = dbc.Select(
    id="dd-equity-disagg",
    options=[{"label": l, "value": l} for l in selected_disaggregation],
    value="Wealth",
    persistence=True,
    persistence_type="session",
)

# %%
# dbc Select NFHS round
dd_equity_round = dbc.Select(
    id="dd-equity-round",
    options=[
        {"label": l, "value": l} for l in ["NFHS-4 (2015-16)", "NFHS-5 (2019-21)"]
    ],
    value="NFHS-5 (2019-21)",
    persistence=True,
    persistence_type="session",
)

# %%
# dbc button: download datatable
bt_dwd_equity = dbc.Button(
    html.P(
        ["Download Table in ", html.Code("csv")],
        style={
            "margin-top": "12px",
            "fontWeight": "bold",
        },
    ),
    id="btn-dwd-equity",
    class_name="me-1",
    outline=True,
    color="info",
)

# %%
# dbc Select Top disaggregation
dd_equity_top = dbc.Select(
    id="dd-equity-top",
    persistence=True,
    persistence_type="session",
)

# %%
# dbc Select Bottom disaggregation
dd_equity_bot = dbc.Select(
    id="dd-equity-bot",
    persistence=True,
    persistence_type="session",
)

# %%
# dbc states data table (coloured-by-type bars + equity)
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select All India or State",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_states_equity,
                        ]
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select NFHS Round",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_equity_round,
                        ]
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Equity Disaggregation",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_equity_disagg,
                        ]
                    ),
                    width="auto",
                ),
                dbc.Col(
                    [bt_dwd_equity, dcc.Download(id="table-dwd-equity")],
                    width="auto",
                    style={"paddingTop": "20px"},
                ),
            ],
            justify="evenly",
            align="center",
        ),
        dbc.Row(
            dbc.Col(dcc.Graph(id="state-equity-plot", figure=label_no_fig), width=12),
            justify="evenly",
            align="center",
        ),
        dbc.Row(
            dbc.Col(
                html.Label(
                    "Equity Table", style={"color": "MidnightBlue", "fontSize": "18px"}
                ),
                width="auto",
            ),
            justify="center",
            align="center",
            style={"paddingTop": "10px"},
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Top Category",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_equity_top,
                        ]
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Bottom Category",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_equity_bot,
                        ]
                    ),
                    width="auto",
                ),
            ],
            justify="center",
            align="center",
            style={"paddingTop": "15px"},
        ),
        dbc.Row(
            dbc.Col(id="table-col-equity", width="auto"),
            justify="evenly",
            align="center",
            style={"paddingTop": "30px", "paddingBottom": "20px"},
        ),
        # hidden div: share data table in Dash
        html.Div(id="df-equity", style={"display": "none"}),
        # share data in Dash with store element
        dcc.Store(id="selections"),
    ],
    fluid=True,
    style={"paddingTop": "20px"},
)


# %%
# bars for total values column
def data_bars(column, row_id, bar_colour):
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    col_max = 1
    col_min = 0
    ranges = [((col_max - col_min) * i) + col_min for i in bounds]
    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        max_bound_percentage = bounds[i] * 100
        styles.append(
            {
                "if": {
                    "filter_query": (
                        "{{{column}}} >= {min_bound}"
                        + (
                            " && {{{column}}} < {max_bound}"
                            if (i < len(bounds) - 1)
                            else ""
                        )
                    ).format(column=column, min_bound=min_bound, max_bound=max_bound),
                    "column_id": column,
                    "row_index": row_id,
                },
                "background": (
                    """
                    linear-gradient(90deg,
                    {bar_colour} 0%,
                    {bar_colour} {max_bound_percentage}%,
                    white {max_bound_percentage}%,
                    white 100%)
                """.format(
                        max_bound_percentage=max_bound_percentage, bar_colour=bar_colour
                    )
                ),
                "paddingBottom": 2,
                "paddingTop": 2,
            }
        )

    return styles


# %%
# customized bars for equity column (per-row based)
def data_equity_bars(
    column,
    row_id,
    row_total,
    row_top,
    row_bot,
    top_colour="#ae4131ff",
    bot_colour="#ff9437ff",
):

    style = [
        {
            "if": {"column_id": column, "row_index": row_id},
            "paddingBottom": 2,
            "paddingTop": 2,
            "background": """
                linear-gradient(90deg,
                white 0%,
                white {limit_inf}%,
                {color_below} {limit_inf}%,
                {color_below} {total_val}%,
                {color_above} {total_val}%,
                {color_above} {limit_sup}%,
                white {limit_sup}%,
                white 100%)
            """.format(
                limit_inf=row_bot * 100 if row_bot < row_top else row_top * 100,
                color_below=bot_colour if row_bot < row_top else top_colour,
                total_val=row_total * 100,
                color_above=top_colour if row_bot < row_top else bot_colour,
                limit_sup=row_top * 100 if row_bot < row_top else row_bot * 100,
            ),
        }
    ]

    return style


# %%
# equity table column names
col_total = "Total value"
col_equity = "Top - Bottom"
# selection of datatable columns to download
sel_col_dwd = [
    "Indicator Type",
    "Indicator",
    col_total,
    col_equity,
    "variable",
    "Disaggregation",
    "Year",
    "State",
]
# create equity datatable function
@callback(
    Output("df-equity", "children"),
    Output("state-equity-plot", "figure"),
    Output("selections", "data"),
    Input("dd-states-equity", "value"),
    Input("dd-equity-round", "value"),
    Input("dd-equity-disagg", "value"),
)
def update_equity_plot(state_value, round_value, disagg_value):

    if disagg_value == "Residence":
        col_map = ["Rural", "Urban"]
        tip_val = ["Urban", "Rural"]
    elif disagg_value == "Wealth":
        col_map = ["Poorest", "Poor", "Middle", "Rich", "Richest"]
        tip_val = ["Richest", "Poorest"]
    elif disagg_value == "Women's Education":
        col_map = [
            "No education",
            "Primary education",
            "Secondary education",
            "Higher education",
        ]
        tip_val = ["Higher education", "No education"]
    elif disagg_value == "Caste":
        col_map = ["SC", "ST", "OBC", "Others"]
        tip_val = ["OBC", "SC"]
    elif disagg_value == "Religion":
        col_map = ["Hindu", "Muslim", "Other"]
        tip_val = ["Hindu", "Muslim"]

    # bar colors
    bar_colors = ["Total", *col_map]
    display_df = (
        df_equity.query("State == @state_value & Year == @round_value")
        .melt(
            id_vars=["Indicator", "State", "Year"],
            value_vars=bar_colors,
        )
        .merge(equity_kpi_type_df, on="Indicator", how="left", sort=False)
        .astype(
            {
                "Indicator_Type": CategoricalDtype(
                    categories=equity_kpi_type_df.Indicator_Type.unique(), ordered=True
                )
            }
        )
        .round({"value": 2})
        .sort_values(by=["Indicator_Type", "Indicator"])
    )

    # display_df in bars
    fig = (
        px.bar(
            display_df,
            x="Indicator",
            y="value",
            color="variable",
            barmode="group",
            title="Equity Plot",
        )
        .update_yaxes(range=[0, 100])
        .update_layout(title_x=0.5, xaxis_title=None)
    )

    # add disaggregation for download reference
    display_df["Disaggregation"] = disagg_value
    # prettify column names
    display_df.rename(
        columns={"value": col_total, "Indicator_Type": "Indicator Type"},
        inplace=True,
    )

    return (
        display_df[[col for col in sel_col_dwd if col != col_equity]].to_json(
            orient="split"
        ),
        fig,
        {"tip_val": tip_val, "col_map": bar_colors},
    )


# %%
# callback to update top bottom selectors
@callback(
    Output("dd-equity-top", "value"),
    Output("dd-equity-top", "options"),
    Output("dd-equity-bot", "value"),
    Output("dd-equity-bot", "options"),
    Input("selections", "data"),
)
def update_top_bottom(data_selected):
    if not data_selected:
        return "", [], "", []
    else:
        return (
            data_selected["tip_val"][0],
            [{"label": l, "value": l} for l in data_selected["col_map"]],
            data_selected["tip_val"][1],
            [{"label": l, "value": l} for l in data_selected["col_map"]],
        )


# %%
# callback to display datatable equity
@callback(
    Output("table-col-equity", "children"),
    Input("df-equity", "children"),
    Input("dd-equity-top", "value"),
    Input("dd-equity-bot", "value"),
)
def update_equity_table(df_equity, top_value, bot_value):
    if not df_equity:
        return None
    else:
        df = pd.read_json(df_equity, orient="split").rename(
            columns={
                "value": col_total,
                "Indicator_Type": "Indicator Type",
            }
        )

        # replace percantage as unit fraction
        df.loc[:, col_total] = df[col_total] / 100
        # refactor dataframe for equity display
        disp_equity_df = df.query("variable=='Total'").set_index("Indicator")

        # calculate top-bottom difference
        disp_equity_df["equity_top"] = df.query("variable==@top_value").set_index(
            "Indicator"
        )[col_total]
        disp_equity_df["equity_bot"] = df.query("variable==@bot_value").set_index(
            "Indicator"
        )[col_total]
        disp_equity_df[col_equity] = (
            disp_equity_df.equity_top - disp_equity_df.equity_bot
        )
        disp_equity_df.reset_index(inplace=True)

        return (
            DataTable(
                data=disp_equity_df.to_dict("records"),
                columns=[
                    {
                        "name": i,
                        "id": i,
                        "type": "numeric",
                        "format": FormatTemplate.percentage(0),
                    }
                    if i in [col_total, col_equity]
                    else {"name": i, "id": i}
                    for i in sel_col_dwd[:4]
                ],
                tooltip_duration=7000,
                tooltip_data=[
                    {
                        col_equity: {
                            "value": "- "
                            + "\n- ".join(
                                [
                                    f"**{a_tip}**: {a_val}%"
                                    for a_tip, a_val in zip(
                                        [top_value, bot_value],
                                        [
                                            round(row["equity_top"] * 100, 2),
                                            round(row["equity_bot"] * 100, 2),
                                        ],
                                    )
                                ]
                            ),
                            "type": "markdown",
                        }
                    }
                    for row in disp_equity_df.to_dict("records")
                ],
                style_cell={
                    "minWidth": "100%",
                    "whiteSpace": "normal",
                    "textAlign": "center",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                },
                style_cell_conditional=[
                    {
                        "if": {"column_id": [col_total]},
                        "width": "130px",
                    }
                ],
                style_data_conditional=sum(
                    [
                        *[
                            data_bars(
                                col_total,
                                list(
                                    disp_equity_df.query(
                                        "`Indicator Type`==@a_type"
                                    ).index
                                ),
                                equity_kpi_types[a_type]["colour"],
                            )
                            for a_type in equity_kpi_types
                        ],
                        # *[
                        #     data_equity_bars(
                        #         col_equity,
                        #         idx,
                        #         row[col_total],
                        #         row.equity_top,
                        #         row.equity_bot,
                        #     )
                        #     for idx, row in disp_equity_df.iterrows()
                        # ],
                    ],
                    [],
                ),
            ),
        )


# %%
# callback to dwd datatable equity
@callback(
    Output("table-dwd-equity", "data"),
    Input("btn-dwd-equity", "n_clicks"),
    State("df-equity", "children"),
)
def download_equity(_, df_plotted):
    if not df_plotted:
        return None
    else:

        df = pd.read_json(df_plotted, orient="split").rename(
            columns={col_total: "value [%]"}
        )
        # replace unit fraction as percantage
        # df.loc[:, "value [%]"] = (df["value [%]"] * 100).round(2)

        return dcc.send_data_frame(
            df.to_csv,
            index=False,
            encoding="utf-8-sig",
            quoting=csv.QUOTE_NONNUMERIC,
            filename="equity_table.csv",
        )
