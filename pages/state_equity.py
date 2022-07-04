from dash import callback, dcc, html, Input, Output, register_page
import dash_bootstrap_components as dbc
import plotly.express as px

from . import df_equity, label_no_fig

register_page(__name__, path="/state_equity", title="State Equity")

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
            style={
                # 'paddingLeft': '25px',
                "marginBottom": "30px",
            },
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
    ],
    fluid=True,
    style={"paddingTop": "20px"},
)

# %%
@callback(
    Output("state-equity-plot", "figure"),
    Output("state-equity-plot-2", "figure"),
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

    display_df = df_equity.query(
        "State == @state_value & Year == 'NFHS-4 (2015-16)'"
    ).melt(
        id_vars=["Indicator", "State"],
        value_vars=col_map,
    )

    display_df_2 = df_equity.query(
        "State == @state_value & Year == 'NFHS-5 (2019-21)'"
    ).melt(
        id_vars=["Indicator", "State"],
        value_vars=col_map,
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

    return fig, fig_2
