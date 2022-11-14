from dash import callback, dcc, html, Input, Output, register_page
from dash.dash_table import DataTable, FormatTemplate
import dash_bootstrap_components as dbc
from pandas.api.types import CategoricalDtype
import plotly.express as px

from . import df_equity, equity_kpi_type_df, equity_kpi_types

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
selected_disaggregation = ["Wealth", "Residence", "Women's Education"]
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
            ],
            justify="evenly",
            align="center",
        ),
        dbc.Row(
            dbc.Col(id="table-col-equity", width="auto"),
            justify="evenly",
            align="center",
            style={"paddingTop": "30px", "paddingBottom": "20px"},
        ),
    ],
    fluid=True,
    style={"paddingTop": "20px"},
)


def data_bars(df, column, row_id, bar_colour):
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
@callback(
    Output("table-col-equity", "children"),
    Input("dd-states-equity", "value"),
    Input("dd-equity-round", "value"),
    Input("dd-equity-disagg", "value"),
)
def update_equity(state_value, round_value, disagg_value):

    if disagg_value == "Residence":
        tip_val = ["Urban", "Rural"]
    elif disagg_value == "Wealth":
        tip_val = ["Richest", "Poorest"]
    elif disagg_value == "Women's Education":
        tip_val = ["Higher education", "No education"]

    display_df = (
        df_equity.query("State == @state_value & Year == @round_value")
        .melt(
            id_vars=["Indicator", "State", "Year"],
            value_vars="Total",
        )
        .merge(equity_kpi_type_df, on="Indicator", how="left", sort=False)
        .astype(
            {
                "Indicator_Type": CategoricalDtype(
                    categories=equity_kpi_type_df.Indicator_Type.unique(), ordered=True
                )
            }
        )
        .sort_values(by=["Indicator_Type", "Indicator"])
    )
    # replace percantage as unit fraction
    display_df.loc[:, "value"] = display_df.value / 100

    return DataTable(
        data=display_df.to_dict("records"),
        columns=[
            {
                "name": i,
                "id": i,
                "type": "numeric",
                "format": FormatTemplate.percentage(0),
            }
            if i == "value"
            else {"name": i, "id": i}
            for i in ["Indicator_Type", "Indicator", "value"]
        ],
        style_cell={
            # all three widths are needed
            # "minWidth": "130px",
            # "width": "130px",
            # "maxWidth": "130px",
            "minWidth": "100%",
            "whiteSpace": "normal",
            "textAlign": "center",
            "overflow": "hidden",
            "textOverflow": "ellipsis",
        },
        style_cell_conditional=[{"if": {"column_id": "value"}, "width": "130px"}],
        style_data_conditional=sum(
            [
                data_bars(
                    display_df,
                    "value",
                    list(display_df.query("Indicator_Type==@a_type").index),
                    equity_kpi_types[a_type]["colour"],
                )
                for a_type in equity_kpi_types
            ],
            [],
        ),
    )
