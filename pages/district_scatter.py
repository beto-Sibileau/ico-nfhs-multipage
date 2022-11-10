from dash import callback, dcc, html, Input, Output, State, register_page
import dash_bootstrap_components as dbc
import dash_treeview_antd
import pandas as pd
import plotly.express as px
import textwrap

from . import (
    data_states,
    nfhs_dist_ind_df,
    district_map_df,
    label_no_fig,
    ind_dom_dist_options,
    district_state_match,
    dist_state_kpi_df,
    df_nfhs_345,
)

register_page(__name__, path="/district-scatter", title="District Scatter")

# %%
# dbc ButtonGroup with RadioItems
scatter_change = html.Div(
    [
        dbc.RadioItems(
            id="radios-scatter-change",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-info",
            labelCheckedClassName="active",
            options=[
                {"label": "NFHS-5 vs. NFHS-4", "value": "rounds"},
                {"label": "Change vs. Change", "value": "change"},
            ],
            value="rounds",
            persistence=True,
            persistence_type="session",
        ),
    ],
    className="radio-group",
)

# dbc select: KPI map domain (x-axis)
dd_domain_x = dbc.Select(
    id="kpi-x-dd",
    size="sm",
    options=ind_dom_dist_options,
    value=ind_dom_dist_options[0]["value"],
    persistence=True,
    persistence_type="session",
    style={"fontSize": "13px"},
)

# dbc select: KPI map domain (y-axis)
dd_domain_y = dbc.Select(
    id="kpi-y-dd",
    size="sm",
    options=ind_dom_dist_options,
    value=ind_dom_dist_options[0]["value"],
    persistence=True,
    persistence_type="session",
    style={"fontSize": "13px"},
)

# %%
states_index = {
    str(i): a_state for i, a_state in enumerate(sorted(data_states, key=str.lower))
}

selection_tree = {
    "title": "All India",
    "key": "0",
    "children": [
        {"title": a_state, "key": "0-" + i} for i, a_state in states_index.items()
    ],
}

# dcc dropdown menu: states selection --> use of dash tree plug in
dd_menu_states = dbc.DropdownMenu(
    label="Active Selection",
    id="selections-button",
    size="md",
    color="info",
    children=html.Div(
        [
            dash_treeview_antd.TreeView(
                id="states_selector",
                multiple=True,
                checkable=True,
                checked=["0"],
                expanded=["0"],
                data=selection_tree,
            ),
        ],
        style={
            "maxHeight": "400px",
            "overflowY": "scroll",
        },
    ),
)

# dbc select: district scatter list 1
dd_district_list_1 = dbc.Select(
    id="kpi-district-list-1",
    size="sm",
    persistence=True,
    persistence_type="session",
    style={"fontSize": "13px"},
)

# dbc select: district scatter list 2
dd_district_list_2 = dbc.Select(
    id="kpi-district-list-2",
    size="sm",
    persistence=True,
    persistence_type="session",
    style={"fontSize": "13px"},
)

# function to return cards layout
# dbc kpi card: https://www.nelsontang.com/blog/2020-07-02-dash-bootstrap-kpi-card/
def create_card(card_title=None, card_num=1):
    card = dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H4(
                        children=card_title if card_title else [],
                        className="card-title",
                        style={"textAlign": "center"},
                        id=f"card-tit-{card_num}",
                    ),
                    html.P(
                        children="N/A",
                        className="card-value",
                        id=f"card-val-{card_num}",
                    ),
                    # note there's card-text bootstrap class ...
                    # html.P(
                    #     "Target: $10.0 M",
                    #     className="card-target",
                    # ),
                    # html.Span([
                    #     html.I(className="fas fa-arrow-circle-up up"),
                    #     html.Span(" 5.5% vs Last Year",
                    #     className="up")
                    # ])
                ]
            )
        ],
        color="info",
        outline=True,
    )
    return card


# %%
# dbc district scatter row
layout = dbc.Container(
    [
        # mantain data until browser/tab closes
        dcc.Store(id="session", storage_type="session"),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Indicator Domain (X-Axis)",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_domain_x,
                        ]
                    ),
                    width=4,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select KPI (X-Axis)",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_district_list_1,
                        ]
                    ),
                    width=8,
                ),
            ],
            justify="evenly",
            align="center",
            style={
                # 'paddingLeft': '25px',
                "marginBottom": "20px",
            },
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Indicator Domain (Y-Axis)",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_domain_y,
                        ]
                    ),
                    width=4,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select KPI (Y-Axis)",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_district_list_2,
                        ]
                    ),
                    width=8,
                ),
            ],
            justify="evenly",
            align="center",
            style={
                # 'paddingLeft': '25px',
                "marginBottom": "20px",
            },
        ),
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "States Selector Tree",
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
                                "Select Axis Definition",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "15px",
                                    "marginBottom": "10px",
                                },
                            ),
                            scatter_change,
                        ],
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
                    dcc.Graph(id="district-plot-scatter", figure=label_no_fig), width=10
                ),
            ],
            justify="evenly",
            align="center",
        ),
        html.Br(),
        dbc.Row(
            [
                dbc.Col(create_card(card_num=2), width="auto"),
            ],
            justify="center",
            align="center",
        ),
        html.Br(),
    ],
    fluid=True,
    style={"paddingTop": "20px"},
)

# %%
# function to return indicator options by domain (sets a value)
@callback(
    Output("kpi-district-list-1", "options"),
    Output("kpi-district-list-1", "value"),
    Output("kpi-district-list-2", "options"),
    Output("kpi-district-list-2", "value"),
    Input("kpi-x-dd", "value"),
    Input("kpi-y-dd", "value"),
)
# update dropdown options: indicator district based on indicator type
def update_district_kpi_options(indicator_domain_x, indicator_domain_y):

    # dbc dropdown allows one selection
    district_kpis_x = sorted(
        nfhs_dist_ind_df.query("ind_domain == @indicator_domain_x").district_kpi.values,
        key=str.lower,
    )
    district_kpis_y = sorted(
        nfhs_dist_ind_df.query("ind_domain == @indicator_domain_y").district_kpi.values,
        key=str.lower,
    )
    return (
        [{"label": l, "value": l} for l in district_kpis_x],
        district_kpis_x[0],
        [{"label": l, "value": l} for l in district_kpis_y],
        district_kpis_y[0],
    )


# %%
# function to work out Active selection
@callback(
    Output("selections-button", "label"),
    Output("session", "data"),
    Input("states_selector", "checked"),
)
# update dropdown options: indicator district based on indicator type
def update_states_selector(checked_tree):

    # checked tree to states
    selected_states = (
        "All India"
        if "0" in checked_tree
        else [states_index[k.split("-")[1]] for k in checked_tree]
    )

    return (
        "Active Selection: "
        + (
            "All India"
            if selected_states == "All India"
            else f"{len(selected_states)} States"
        ),
        dict(
            states=selected_states,
        ),
    )


# %%
@callback(
    Output("district-plot-scatter", "figure"),
    Output("card-tit-2", "children"),
    Output("card-val-2", "children"),
    Input("radios-scatter-change", "value"),
    Input("session", "data"),
    Input("kpi-district-list-1", "value"),
    Input("kpi-district-list-2", "value"),
    State("kpi-x-dd", "value"),
    State("kpi-y-dd", "value"),
)
def update_scatter(
    value_or_change, state_values, kpi_1, kpi_2, distr_dmn_x, distr_dmn_y
):

    if not state_values:
        return label_no_fig, [], "N/A"

    # query dataframe
    kpi_list = [kpi_1, kpi_2]
    display_df = (
        district_map_df.query(
            "State in @state_values['states'] & variable in @kpi_list"
            if state_values["states"] != "All India"
            else "variable in @kpi_list"
        )
        .pivot(
            index=["State", "District name"],
            columns=["variable", "Round"],
            values="value",
        )
        .reset_index()
    )

    if display_df.empty:
        return label_no_fig, [], "N/A"
    else:
        # computation of changes
        display_df[(kpi_1, "NFHS-5 minus NFHS-4")] = (
            display_df.set_index(["State", "District name"])[(kpi_1, "NFHS-5")]
            - display_df.set_index(["State", "District name"])[(kpi_1, "NFHS-4")]
        ).reset_index()[0]
        display_df[(kpi_2, "NFHS-5 minus NFHS-4")] = (
            display_df.set_index(["State", "District name"])[(kpi_2, "NFHS-5")]
            - display_df.set_index(["State", "District name"])[(kpi_2, "NFHS-4")]
        ).reset_index()[0]

        # rejoin columns
        display_df.columns = [
            (" (".join(a_name) + ")").removesuffix(" ()")
            for a_name in display_df.columns.to_flat_index()
        ]

        # rename columns
        kpi_1 = (
            " (".join(
                [
                    kpi_1,
                    (
                        "NFHS-4"
                        if value_or_change == "rounds"
                        else "NFHS-5 minus NFHS-4"
                    ),
                ]
            )
        ) + ")"
        kpi_2 = (
            " (".join(
                [
                    kpi_2,
                    (
                        "NFHS-5"
                        if value_or_change == "rounds"
                        else "NFHS-5 minus NFHS-4"
                    ),
                ]
            )
        ) + ")"
        scatter_fig = (
            px.scatter(
                display_df,
                x=kpi_1,
                y=kpi_2,
                color="State",
                opacity=0.5,
                trendline="ols",
                trendline_scope="overall",
                title=(
                    "Analysis of Indicators: NFHS-5 vs. NFHS-4"
                    if value_or_change == "rounds"
                    else "Analysis of Indicators Change: NFHS-5 minus NFHS-4"
                ),
                hover_data=["District name"],
                height=600,
                labels={
                    kpi_1: (
                        "NFHS-4 Value"
                        if value_or_change == "rounds"
                        else "NFHS (5-4) Change (X-Axis)"
                    ),
                    kpi_2: (
                        "NFHS-5 Value"
                        if value_or_change == "rounds"
                        else "NFHS (5-4) Change (Y-Axis)"
                    ),
                },
            )
            .update_layout(title_x=0.5)
            .update_traces(marker=dict(size=14))
            .update_yaxes(
                title="<br>".join(
                    textwrap.wrap(
                        (
                            kpi_2
                            if value_or_change == "rounds"
                            else "Change in " + kpi_2
                        ),
                        width=70,
                    )
                ),
                title_font=dict(size=11),
            )
            .update_xaxes(
                title="<br>".join(
                    textwrap.wrap(
                        (
                            kpi_1
                            if value_or_change == "rounds"
                            else "Change in " + kpi_1
                        ),
                        width=70,
                    )
                ),
                title_font=dict(size=11),
            )
        )

        # mean: All India unless one State Selected
        match_state = (
            district_state_match.get(
                state_values["states"][0], state_values["states"][0]
            )
            if len(state_values["states"]) == 1
            else "All India"
        )
        # also match with states indicators
        query_str_1 = (
            "Dom_in_Dist == @distr_dmn_x & kpi_district == @kpi_1.removesuffix(' (NFHS-4)')"
            if value_or_change == "rounds"
            else "Dom_in_Dist == @distr_dmn_x & kpi_district == @kpi_1.removesuffix(' (NFHS-5 minus NFHS-4)')"
        )
        match_kpi_1 = dist_state_kpi_df.query(query_str_1)
        query_str_2 = (
            "Dom_in_Dist == @distr_dmn_y & kpi_district == @kpi_2.removesuffix(' (NFHS-5)')"
            if value_or_change == "rounds"
            else "Dom_in_Dist == @distr_dmn_y & kpi_district == @kpi_2.removesuffix(' (NFHS-5 minus NFHS-4)')"
        )
        match_kpi_2 = dist_state_kpi_df.query(query_str_2)
        x_avg = (
            None
            if pd.isna(*match_kpi_1.kpi_state)
            else (
                df_nfhs_345.query(
                    "State == @match_state & `Indicator Type` == @match_kpi_1.Dom_in_State.values[0] & Indicator == @match_kpi_1.kpi_state.values[0] & NFHS == 'NFHS 4'"
                ).Total.values
                if value_or_change == "rounds"
                else (
                    df_nfhs_345.query(
                        "State == @match_state & `Indicator Type` == @match_kpi_1.Dom_in_State.values[0] & Indicator == @match_kpi_1.kpi_state.values[0] & NFHS == 'NFHS 5'"
                    )
                    .set_index("State")
                    .Total
                    - df_nfhs_345.query(
                        "State == @match_state & `Indicator Type` == @match_kpi_1.Dom_in_State.values[0] & Indicator == @match_kpi_1.kpi_state.values[0] & NFHS == 'NFHS 4'"
                    )
                    .set_index("State")
                    .Total
                ).values
            )
        )
        y_avg = (
            None
            if pd.isna(*match_kpi_2.kpi_state)
            else (
                df_nfhs_345.query(
                    "State == @match_state & `Indicator Type` == @match_kpi_2.Dom_in_State.values[0] & Indicator == @match_kpi_2.kpi_state.values[0] & NFHS == 'NFHS 5'"
                ).Total.values
                if value_or_change == "rounds"
                else (
                    df_nfhs_345.query(
                        "State == @match_state & `Indicator Type` == @match_kpi_2.Dom_in_State.values[0] & Indicator == @match_kpi_2.kpi_state.values[0] & NFHS == 'NFHS 5'"
                    )
                    .set_index("State")
                    .Total
                    - df_nfhs_345.query(
                        "State == @match_state & `Indicator Type` == @match_kpi_2.Dom_in_State.values[0] & Indicator == @match_kpi_2.kpi_state.values[0] & NFHS == 'NFHS 4'"
                    )
                    .set_index("State")
                    .Total
                ).values
            )
        )

        # adjust scales for comparisson
        x_min = display_df[kpi_1].min()
        y_min = display_df[kpi_2].min()
        x_max = display_df[kpi_1].max()
        y_max = display_df[kpi_2].max()
        # use same range to compare rounds
        full_range = [[x_min, y_min], [x_max, y_max]]

        # x_avg = display_df[kpi_1].mean()
        if x_avg:
            scatter_fig.add_vline(
                x=x_avg[0], line_dash="dash", line_width=3, line_color="green"
            ).update_traces(line_width=3)
            # add text annotation to avg X
            scatter_fig.add_annotation(
                x=x_avg[0],
                y=full_range[1][1],
                text=f"{match_state} "
                + ("Mean-X: " if value_or_change == "rounds" else "Mean Change-X: ")
                + f"{x_avg[0]:.0f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                arrowsize=1.5,
                font={"color": "green"},
            )

        # y_avg = display_df[kpi_2].mean()
        if y_avg:
            scatter_fig.add_hline(
                y=y_avg[0], line_dash="dash", line_width=3, line_color="green"
            ).update_traces(line_width=3)
            # add text annotation to avg Y
            scatter_fig.add_annotation(
                x=full_range[1][0],
                y=y_avg[0],
                xanchor="left",
                text=f"{match_state} "
                + ("Mean-Y: " if value_or_change == "rounds" else "Mean Change-Y: ")
                + f"{y_avg[0]:.0f}",
                showarrow=True,
                arrowhead=2,
                arrowcolor="green",
                arrowsize=1.5,
                font={"color": "green"},
            )

        r_sq = round(
            px.get_trendline_results(scatter_fig).px_fit_results.iloc[0].rsquared, 2
        )
        scatter_fig.data[
            -1
        ].hovertemplate = f"<b>OLS trendline</b><br>R<sup>2</sup>={r_sq}"

        return (
            scatter_fig,
            # card title
            f"Relationship between {'NFHS-4 and NFHS-5' if value_or_change == 'rounds' else 'changes in NFHS-5 minus NFHS-4'} for Selected Indicators",
            # card value
            f"R2 of the correlation: {r_sq}",
        )
