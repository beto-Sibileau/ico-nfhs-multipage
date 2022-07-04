from dash import callback, dcc, html, Input, Output, register_page
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px

from . import (
    state_options,
    district_map_options,
    district_kpi_map,
    label_no_fig,
    kpi_color_inverse,
    district_map_df,
    geo_dict,
    district_geo_dict,
    geo_json_dict,
)

register_page(__name__, path="/district_gis", title="District GIS")

# dbc select: KPI district map --> All India or States
# restricted to States only (All India requires more resources to deploy)
dd_india_or_state = dbc.Select(
    id="india-or-state-dd",
    size="sm",
    options=state_options,
    value="Kerala",
    persistence=True,
)

# dbc select: KPI district map
dd_kpi_map_district = dbc.Select(
    id="kpi-district-map-dd",
    size="sm",
    options=district_map_options,
    value=district_kpi_map[0],
    persistence=True,
)

# dbc district kpi map row
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select a State",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_india_or_state,
                        ]
                    ),
                    width="auto",
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
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_kpi_map_district,
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
                    html.Div(
                        [
                            html.P(
                                "NFHS-4 (2015-16)",
                                style={
                                    "fontWeight": "normal",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "Blue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dcc.Graph(id="district-plot", figure=label_no_fig),
                        ]
                    ),
                    width=5,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "NFHS-5 (2019-21)",
                                style={
                                    "fontWeight": "normal",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "Blue",
                                    "fontSize": "16px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dcc.Graph(id="district-plot-r2", figure=label_no_fig),
                        ]
                    ),
                    width=5,
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
# function to avoid figure display inline
def update_cm_fig(cm_fig):
    cm_fig.update_geos(fitbounds="locations", visible=False)
    cm_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return cm_fig


# color names for scale
color_names = ["Navy", "FloralWhite", "DarkRed"]
# customed continous scale
red_y_blue = [[0, color_names[0]], [0.5, color_names[1]], [1, color_names[2]]]
# customed continous scale: gray NaNs
color_nan = "gray"
nan_blue_y_red = [
    [0, color_nan],
    [0.001, color_nan],
    [0.001, color_names[0]],
    [0.5, color_names[1]],
    [1, color_names[2]],
]
nan_red_y_blue = [
    [0, color_nan],
    [0.001, color_nan],
    [0.001, color_names[2]],
    [0.5, color_names[1]],
    [1, color_names[0]],
]


@callback(
    Output("district-plot", "figure"),
    Output("district-plot-r2", "figure"),
    Input("india-or-state-dd", "value"),
    Input("kpi-district-map-dd", "value"),
    # Input('nfhs-round-dd', 'value'),
)
# use dropdown values: update geo-json and indicator in map (district-wise)
def disp_in_district_map(india_or_state, distr_kpi):

    # test if all_india
    if india_or_state == "All India":
        # query dataframe
        display_df = district_map_df.query(
            "variable == @distr_kpi & Round == 'NFHS-4'"
        ).reset_index(drop=True)
        display_df_r2 = district_map_df.query(
            "variable == @distr_kpi & Round == 'NFHS-5'"
        ).reset_index(drop=True)
        # do not filter geojson
        geofile = geo_json_dict
    else:
        # query dataframe
        display_df = district_map_df.query(
            "State == @india_or_state & variable == @distr_kpi & Round == 'NFHS-4'"
        ).reset_index(drop=True)
        display_df_r2 = district_map_df.query(
            "State == @india_or_state & variable == @distr_kpi & Round == 'NFHS-5'"
        ).reset_index(drop=True)
        # filter geojson by state
        geofile = {}
        geofile["type"] = "FeatureCollection"
        geofile["features"] = geo_dict[india_or_state]

    # min-max block kpis - before setting missing as negatives
    district_kpi_min = display_df.value.min()
    district_kpi_max = display_df.value.max()
    # min-max block kpis - before setting missing as negatives
    district_kpi_min_2 = display_df_r2.value.min()
    district_kpi_max_2 = display_df_r2.value.max()
    # use same range to compare rounds
    full_range = [
        pd.Series([district_kpi_min, district_kpi_min_2]).min() - 0.1,
        pd.Series([district_kpi_max, district_kpi_max_2]).max(),
    ]

    # set missing reporting districts
    not_reported = np.setdiff1d(
        district_geo_dict[india_or_state]["District name"].values,
        display_df["District name"].values,
    )
    not_reported_geo = [
        district_geo_dict[india_or_state]
        .query("`District name` == @a_name")
        .District_geo.values[0]
        for a_name in not_reported
    ]
    # concat not_reported as negatives
    display_df = pd.concat(
        [
            display_df,
            pd.DataFrame(
                {
                    "District_geo": not_reported_geo,
                    "District_name": not_reported,
                }
            ),
        ],
        ignore_index=True,
    ).fillna(-1)

    # set missing reporting districts r2
    not_reported_r2 = np.setdiff1d(
        district_geo_dict[india_or_state]["District name"].values,
        display_df_r2["District name"].values,
    )
    not_reported_geo_r2 = [
        district_geo_dict[india_or_state]
        .query("`District name` == @a_name")
        .District_geo.values[0]
        for a_name in not_reported_r2
    ]
    # concat not_reported as negatives
    display_df_r2 = pd.concat(
        [
            display_df_r2,
            pd.DataFrame(
                {
                    "District_geo": not_reported_geo_r2,
                    "District_name": not_reported_r2,
                }
            ),
        ],
        ignore_index=True,
    ).fillna(-1)

    # scale according to indicator
    dyn_color_scale = (
        nan_blue_y_red if distr_kpi in kpi_color_inverse else nan_red_y_blue
    )

    # district map
    cmap_fig = px.choropleth(
        display_df,
        geojson=geofile,
        featureidkey="properties.707_dist_7",  # 'properties.ST_NM', #
        locations="District_geo",
        color="value",
        # color_continuous_scale = "RdBu",
        color_continuous_scale=dyn_color_scale,
        range_color=full_range,
        # color_discrete_map={'red':'red', 'orange':'orange', 'green':'green'},
        # hover_data=[dd_value],
        projection="mercator",
    )

    # district map - round 2
    cmap_fig_r2 = px.choropleth(
        display_df_r2,
        geojson=geofile,
        featureidkey="properties.707_dist_7",  # 'properties.ST_NM', #
        locations="District_geo",
        color="value",
        # color_continuous_scale = "RdBu",
        color_continuous_scale=dyn_color_scale,
        range_color=full_range,
        # color_discrete_map={'red':'red', 'orange':'orange', 'green':'green'},
        # hover_data=[dd_value],
        projection="mercator",
    )

    return update_cm_fig(cmap_fig), update_cm_fig(cmap_fig_r2)


# %%
# pages layout

# # div district map row
# dcc.Loading(
#     children=html.Div(
#         [district_map_row],
#         style={
#             "paddingTop": "20px",
#         },
#     ),
#     id="loading-map",
#     type="circle",
#     fullscreen=True,
# ),
# html.Hr(
#     style={
#         "color": "DeepSkyBlue",
#         "height": "3px",
#         "margin-top": "30px",
#         "margin-bottom": "0",
#     }
# ),
