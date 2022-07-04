from dash import callback, dcc, html, Input, Output, register_page
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px

from . import (
    state_options,
    district_map_options,
    district_kpi_map,
    district_map_df,
    label_no_fig,
    nfhs_345_states,
    nfhs_345_ind_df,
)

register_page(__name__, path="/district_scatter", title="District Scatter")

# %%
# dcc dropdown: states --> dcc allows multi, styling not as dbc
dd_states = dcc.Dropdown(
    id="my-states-dd",
    options=state_options,
    value="Kerala",
    multi=True,
)

# dbc select: district scatter list 1
dd_district_list_1 = dbc.Select(
    id="kpi-district-list-1",
    size="sm",
    options=district_map_options,
    value=district_kpi_map[10],
)

# dbc select: district scatter list 2
dd_district_list_2 = dbc.Select(
    id="kpi-district-list-2",
    size="sm",
    options=district_map_options,
    value=district_kpi_map[14],
)

# %%
# dbc district scatter row
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select State/s",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_states,
                        ],
                        style={"font-size": "75%"},
                    ),
                    width=2,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select KPI 1",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_district_list_1,
                        ]
                    ),
                    width=5,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select KPI 2",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_district_list_2,
                        ]
                    ),
                    width=5,
                ),
            ],
            justify="evenly",
            align="center",
            style={
                # 'paddingLeft': '25px',
                "marginBottom": "25px",
            },
        ),
        # dbc.Row([
        #     dbc.Col(
        #         button_group_nfhs,
        #         width="auto"
        #     ),
        # ], justify="start", align="start", style={'paddingLeft': '25px'}),
        dbc.Row(
            [
                dbc.Col(
                    dcc.Graph(id="district-plot-scatter", figure=label_no_fig), width=6
                ),
                dbc.Col(
                    dcc.Graph(id="district-plot-scatter-2", figure=label_no_fig),
                    width=6,
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
    Output("district-plot-scatter", "figure"),
    Output("district-plot-scatter-2", "figure"),
    Input("my-states-dd", "value"),
    Input("kpi-district-list-1", "value"),
    Input("kpi-district-list-2", "value"),
)
def update_scatter(state_values, kpi_1, kpi_2):

    if not state_values:
        return label_no_fig, label_no_fig

    # query dataframe
    kpi_list = [kpi_1, kpi_2]
    display_df = (
        district_map_df.query(
            "State in @state_values & variable in @kpi_list & Round == 'NFHS-4'"
        )
        .pivot(
            index=["State", "District name"],
            columns="variable",
            values="value",
        )
        .reset_index()
    )

    display_df_2 = (
        district_map_df.query(
            "State in @state_values & variable in @kpi_list & Round == 'NFHS-5'"
        )
        .pivot(
            index=["State", "District name"],
            columns="variable",
            values="value",
        )
        .reset_index()
    )

    if display_df.empty or display_df_2.empty:
        return label_no_fig, label_no_fig
    else:
        scatter_fig = (
            px.scatter(
                display_df,
                x=kpi_1,
                y=kpi_2,
                color="State",
                opacity=0.5,
                trendline="ols",
                trendline_scope="overall",
                title="NFHS-4 (2015-16)",
                hover_data=["District name"],
            )
            .update_traces(marker=dict(size=16))
            .update_yaxes(title_font=dict(size=11))
            .update_xaxes(title_font=dict(size=11))
        )
        x_avg = display_df[kpi_1].mean()
        scatter_fig.add_vline(
            x=x_avg, line_dash="dash", line_width=3, line_color="green"
        ).update_traces(line_width=3)
        y_avg = display_df[kpi_2].mean()
        scatter_fig.add_hline(
            y=y_avg, line_dash="dash", line_width=3, line_color="green"
        ).update_traces(line_width=3)

        scatter_fig_2 = (
            px.scatter(
                display_df_2,
                x=kpi_1,
                y=kpi_2,
                color="State",
                opacity=0.5,
                trendline="ols",
                trendline_scope="overall",
                title="NFHS-5 (2019-21)",
                hover_data=["District name"],
            )
            .update_traces(marker=dict(size=16))
            .update_yaxes(title_font=dict(size=11))
            .update_xaxes(title_font=dict(size=11))
        )
        x_avg_2 = display_df_2[kpi_1].mean()
        scatter_fig_2.add_vline(
            x=x_avg_2, line_dash="dash", line_width=3, line_color="green"
        ).update_traces(line_width=3)
        y_avg_2 = display_df_2[kpi_2].mean()
        scatter_fig_2.add_hline(
            y=y_avg_2, line_dash="dash", line_width=3, line_color="green"
        ).update_traces(line_width=3)

        # adjust scales for comparisson
        x_min = display_df[kpi_1].min()
        y_min = display_df[kpi_2].min()
        x_min_2 = display_df_2[kpi_1].min()
        y_min_2 = display_df_2[kpi_2].min()
        x_max = display_df[kpi_1].max()
        y_max = display_df[kpi_2].max()
        x_max_2 = display_df_2[kpi_1].max()
        y_max_2 = display_df_2[kpi_2].max()
        # use same range to compare rounds
        full_range = [
            [
                pd.Series([x_min, x_min_2]).min() * 0.9,
                pd.Series([y_min, y_min_2]).min() * 0.9,
            ],
            [
                pd.Series([x_max, x_max_2]).max() * 1.1,
                pd.Series([y_max, y_max_2]).max() * 1.1,
            ],
        ]
        # update axis in scatters
        scatter_fig.update_xaxes(range=[full_range[0][0], full_range[1][0]])
        scatter_fig.update_yaxes(range=[full_range[0][1], full_range[1][1]])
        scatter_fig_2.update_xaxes(range=[full_range[0][0], full_range[1][0]])
        scatter_fig_2.update_yaxes(range=[full_range[0][1], full_range[1][1]])

    # check for missing reported indicators for NFHS rounds
    plot_1_flag = display_df.dropna(axis=1, how="all").shape[1] < display_df.shape[1]
    plot_2_flag = (
        display_df_2.dropna(axis=1, how="all").shape[1] < display_df_2.shape[1]
    )

    if plot_1_flag & plot_2_flag:
        return label_no_fig, label_no_fig
    elif plot_1_flag:
        r_sq_2 = round(
            px.get_trendline_results(scatter_fig_2).px_fit_results.iloc[0].rsquared, 2
        )
        scatter_fig_2.data[
            -1
        ].hovertemplate = f"<b>OLS trendline</b><br>R<sup>2</sup>={r_sq_2}"
        return label_no_fig, scatter_fig_2
    elif plot_2_flag:
        r_sq = round(
            px.get_trendline_results(scatter_fig).px_fit_results.iloc[0].rsquared, 2
        )
        scatter_fig.data[
            -1
        ].hovertemplate = f"<b>OLS trendline</b><br>R<sup>2</sup>={r_sq}"
        return scatter_fig, label_no_fig
    else:
        r_sq = round(
            px.get_trendline_results(scatter_fig).px_fit_results.iloc[0].rsquared, 2
        )
        scatter_fig.data[
            -1
        ].hovertemplate = f"<b>OLS trendline</b><br>R<sup>2</sup>={r_sq}"
        r_sq_2 = round(
            px.get_trendline_results(scatter_fig_2).px_fit_results.iloc[0].rsquared, 2
        )
        scatter_fig_2.data[
            -1
        ].hovertemplate = f"<b>OLS trendline</b><br>R<sup>2</sup>={r_sq_2}"
        return scatter_fig, scatter_fig_2
