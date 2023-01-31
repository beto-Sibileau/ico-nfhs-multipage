from dash import callback, dcc, html, Input, Output, register_page
import dash_bootstrap_components as dbc
import dash_treeview_antd
import numpy as np
import pandas as pd
import plotly.express as px

from . import (
    nfhs_345_states,
    nfhs_345_ind_types,
    df_nfhs_345,
    label_no_fig,
    states_kpi_index,
)

register_page(__name__, path="/state-trend", title="State Trends")

# %%
# nfhs_345_states is sorted at init
states_index = {str(i): a_state for i, a_state in enumerate(nfhs_345_states)}

selection_tree = {
    "title": "",
    "key": "0",
    "children": [
        {"title": a_state, "key": "0-" + i} for i, a_state in states_index.items()
    ],
}

# dbc dd menu + dash tree (same selection in scatter, but states name from Rakesh Excel)
dd_menu_states = dbc.DropdownMenu(
    label="Active Selection",
    id="dd-select-state",
    size="md",
    color="info",
    children=html.Div(
        [
            dash_treeview_antd.TreeView(
                id="states-selected",
                multiple=True,
                checkable=True,
                checked=["0-0"],
                data=selection_tree,
            ),
        ],
        style={
            "maxHeight": "400px",
            "overflowY": "scroll",
        },
    ),
)

# %%
# selection tree for kpis
kpi_selection_tree = {
    "title": "",
    "key": "0",
    "children": [
        {
            "title": ind_type,
            "key": "0-" + str(i),
            "children": [
                {"title": indicator, "key": "0-" + k}
                for k, indicator in states_kpi_index.items()
                if k.split("-")[0] == str(i)
            ],
        }
        for i, ind_type in enumerate(nfhs_345_ind_types)
    ],
}

# dbc dd menu + dash tree (kpi selection by indicator type)
dd_menu_state_kpis = dbc.DropdownMenu(
    label="Active Selection",
    id="dd-select-state-kpi",
    size="md",
    color="info",
    align_end=True,
    children=html.Div(
        [
            dash_treeview_antd.TreeView(
                id="kpis-selected",
                multiple=True,
                checkable=True,
                checked=["0-16-0"],
                expanded=["0-16"],
                data=kpi_selection_tree,
            ),
        ],
        style={
            "maxHeight": "400px",
            "overflowY": "scroll",
        },
    ),
)

# %%
# dbc select: residence disaggregation
dd_residence = dbc.Select(
    id="dd-residence",
    size="md",
    persistence=True,
    persistence_type="session",
    options=[{"label": l, "value": l} for l in ["Total", "Urban", "Rural"]],
    value="Total",
)

# %%
# dbc state trends row
layout = dbc.Container(
    [
        # mantain data until browser/tab closes
        dcc.Store(id="trend-session", storage_type="session"),
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
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_menu_states,
                        ],
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select KPI/s",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_menu_state_kpis,
                        ],
                    ),
                    width="auto",
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Residence",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_residence,
                        ]
                    ),
                    width="auto",
                ),
            ],
            justify="evenly",
            align="center",
        ),
        html.Br(),
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
    Output("dd-select-state", "label"),
    Output("dd-select-state-kpi", "label"),
    Output("trend-session", "data"),
    Input("states-selected", "checked"),
    Input("kpis-selected", "checked"),
)
# state and kpi dash trees: prevent select all
def update_selectors(checked_states, checked_kpis):

    selected_states = [
        states_index[k.removeprefix("0-")] for k in checked_states if k != "0"
    ]
    selected_kpis = [
        states_kpi_index[k.removeprefix("0-")]
        for k in checked_kpis
        if len(k.split("-")) == 3
    ]

    selected_states_label = "Active Selection: " + (
        "All India"
        if "All India" in selected_states and len(selected_states) == 1
        else (
            f"All India and {len(selected_states)-1} States"
            if "All India" in selected_states
            else f"{len(selected_states)} States"
        )
    )
    selected_kpis_label = f"Active Selection: {len(selected_kpis)} KPIs"

    return (
        selected_states_label,
        selected_kpis_label,
        dict(states=selected_states, kpis=selected_kpis),
    )


# %%
@callback(
    Output("state-trend-plot", "figure"),
    Input("trend-session", "data"),
    Input("dd-residence", "value"),
)
def update_trend(selections, residence):

    state_values = selections["states"]
    kpi_values = selections["kpis"]

    if not state_values or not kpi_values:
        return label_no_fig
    elif len(state_values) * len(kpi_values) > 500:
        # limit maximum number of series
        return label_no_fig

    display_df = (
        df_nfhs_345.query("State in @state_values & Indicator in @kpi_values")
        .melt(
            id_vars=["Indicator", "State", "NFHS", "Year (give as a period)"],
            value_vars=residence,  # ["Urban", "Rural", "Total"],
        )
        .dropna(subset="value")
        # probably the duplicates appeared by missing gender annotations
        .drop_duplicates(
            subset=["State", "Indicator", "Year (give as a period)", "variable"]
        )
        .sort_values(
            ["Year (give as a period)", "State", "Indicator"],
            ignore_index=True,
        )
        .astype({"value": "float64"})
    )

    if display_df.empty:
        return label_no_fig
    else:
        # prettify indicator name
        display_df.loc[:, "Indicator"] = display_df.Indicator.str.wrap(50).apply(
            lambda x: x.replace("\n", "<br>")
        )
        display_df.set_index(["State", "Indicator"], inplace=True)
        trend_fig = px.line(
            display_df,
            x="Year (give as a period)",
            y="value",
            labels={"Year (give as a period)": "Year", "variable": "Residence"},
            color=list(display_df.index),
            line_shape="spline",
            render_mode="svg,",
            hover_data=["NFHS", "variable"],
        ).update_traces(mode="lines+markers")

        trend_fig.update_layout(
            legend=dict(font=dict(size=8), y=0.5, x=1.01),
            margin_t=20,
            # margin_l=40,
            # margin_r=20,
        )

        return trend_fig
