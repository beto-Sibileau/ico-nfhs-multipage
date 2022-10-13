from dash import callback, dcc, html, Input, Output, register_page
from dash.dash_table import DataTable, FormatTemplate
import dash_bootstrap_components as dbc
import plotly.express as px

from . import df_equity, label_no_fig

register_page(__name__, path="/state-equity", title="State Equity")

# %%
# dbc select: all india or states for equity
union_territories = [
    "Andaman and Nicobar Islands",
    "Dadra and Nagar Haveli",
    "Daman and Diu",
    "Chandigarh",
    "Lakshadweep",
    "Puducherry",
    "Ladakh",
]

# names to display in dropdown equity
states_4_equity = df_equity.State.unique()

dd_states_equity = dbc.Select(
    id="dd-states-equity",
    options=[
        {"label": l, "value": l}
        for l in sorted(states_4_equity, key=str.lower)
        if l not in union_territories
    ],
    value="All India",
    persistence=True,
    persistence_type="session",
)

# %%
# dbc ButtonGroup with RadioItems
button_group_disagg = html.Div(
    [
        dbc.RadioItems(
            id="radios-disagg",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-info",
            labelCheckedClassName="active",
            options=[
                {"label": "Residence", "value": "Residence"},
                {"label": "Wealth", "value": "Wealth"},
                {"label": "Women's Education", "value": "Women's Education"},
                {"label": "Caste", "value": "Caste"},
                {"label": "Religion", "value": "Religion"},
            ],
            value="Residence",
            persistence=True,
            persistence_type="session",
        ),
    ],
    className="radio-group",
)

# %%
# dbc states equity bar row
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
                                "Select Disaggregation",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            button_group_disagg,
                        ]
                    ),
                    width="auto",
                ),
            ],
            justify="evenly",
            align="center",
        ),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="state-equity-plot", figure=label_no_fig), width=6
                ),
                dbc.Col(
                    dcc.Graph(id="state-equity-plot-2", figure=label_no_fig), width=6
                ),
            ],
            justify="evenly",
            align="center",
        ),
        dbc.Row(
            dbc.Col(id="table-col-equity", width="auto"),
            justify="evenly",
            align="center",
            style={"paddingTop": "20px", "paddingBottom": "20px"},
        ),
    ],
    fluid=True,
    style={"paddingTop": "20px"},
)


def data_bars_diverging(df, column, color_above="#3D9970", color_below="#FF4136"):
    n_bins = 100
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    col_max = 1
    col_min = -1
    ranges = [((col_max - col_min) * i) + col_min for i in bounds]
    midpoint = 0

    styles = []
    for i in range(1, len(bounds)):
        min_bound = ranges[i - 1]
        max_bound = ranges[i]
        min_bound_percentage = bounds[i - 1] * 100
        max_bound_percentage = bounds[i] * 100

        style = {
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
            },
            "paddingBottom": 2,
            "paddingTop": 2,
        }
        if max_bound > midpoint:
            background = """
                    linear-gradient(90deg,
                    white 0%,
                    white 50%,
                    {color_above} 50%,
                    {color_above} {max_bound_percentage}%,
                    white {max_bound_percentage}%,
                    white 100%)
                """.format(
                max_bound_percentage=max_bound_percentage, color_above=color_above
            )
        else:
            background = """
                    linear-gradient(90deg,
                    white 0%,
                    white {min_bound_percentage}%,
                    {color_below} {min_bound_percentage}%,
                    {color_below} 50%,
                    white 50%,
                    white 100%)
                """.format(
                min_bound_percentage=min_bound_percentage, color_below=color_below
            )
        style["background"] = background
        styles.append(style)

    return styles


# %%
@callback(
    Output("state-equity-plot", "figure"),
    Output("state-equity-plot-2", "figure"),
    Output("table-col-equity", "children"),
    Input("dd-states-equity", "value"),
    Input("radios-disagg", "value"),
)
def update_equity(state_value, disagg_value):

    if disagg_value == "Residence":
        col_map = ["Total", "Rural", "Urban"]
    elif disagg_value == "Wealth":
        col_map = ["Poorest", "Poor", "Middle", "Rich", "Richest"]
    elif disagg_value == "Women's Education":
        col_map = [
            "No education",
            "Primary education",
            "Secondary education",
            "Higher education",
        ]
    elif disagg_value == "Caste":
        col_map = ["SC", "ST", "OBC", "Others"]
    else:
        col_map = ["Hindu", "Muslim", "Other"]

    display_df = (
        df_equity.query("State == @state_value & Year == 'NFHS-4 (2015-16)'")
        .melt(
            id_vars=["Indicator", "State"],
            value_vars=col_map,
        )
        .sort_values(by="Indicator")
    )

    display_df_2 = (
        df_equity.query("State == @state_value & Year == 'NFHS-5 (2019-21)'")
        .melt(
            id_vars=["Indicator", "State"],
            value_vars=col_map,
        )
        .sort_values(by="Indicator")
    )

    fig = px.bar(
        display_df,
        x="Indicator",
        y="value",
        color="variable",
        barmode="group",
        title="NFHS-4 (2015-16)",
    ).update_yaxes(range=[0, 100])

    fig_2 = px.bar(
        display_df_2,
        x="Indicator",
        y="value",
        color="variable",
        barmode="group",
        title="NFHS-5 (2019-21)",
    ).update_yaxes(range=[0, 100])

    table_df = (
        (
            (
                display_df_2.pivot(
                    index=["variable"],
                    columns="Indicator",
                    values="value",
                )
                - display_df.pivot(
                    index=["variable"],
                    columns="Indicator",
                    values="value",
                )
            )
            / display_df.pivot(
                index=["variable"],
                columns="Indicator",
                values="value",
            )
        )
        .reset_index()
        .sort_values(
            by="variable",
            key=lambda x: x.map({k: v for k, v in zip(col_map, range(len(col_map)))}),
        )
        .rename(columns={"variable": "Disaggregation"})
    )

    return (
        fig,
        fig_2,
        DataTable(
            data=table_df.to_dict("records"),
            columns=[
                {
                    "name": i,
                    "id": i,
                    "type": "numeric",
                    "format": FormatTemplate.percentage(0),
                }
                if "variable" not in i
                else {"name": i, "id": i}
                for i in table_df.columns
            ],
            style_cell={
                # all three widths are needed
                "minWidth": "130px",
                "width": "130px",
                "maxWidth": "130px",
                "whiteSpace": "normal",
                "textAlign": "center",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
            },
            style_data_conditional=(
                data_bars_diverging(table_df, "ANC4+")
                + data_bars_diverging(table_df, "Any ANC")
                + data_bars_diverging(
                    table_df, "C-section delivery", "#FF4136", "#3D9970"
                )
                + data_bars_diverging(table_df, "IFA for 100 days")
                + data_bars_diverging(table_df, "Institutional delivery")
                + data_bars_diverging(table_df, "Neonatal Protection")
            ),
        ),
    )
