import csv
from dash import callback, dcc, html, Input, Output, State, register_page
from dash.dash_table import DataTable, FormatTemplate, Format
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.express as px
import os
import re
import tempfile
from zipfile import ZipFile

from . import (
    state_options,
    label_no_fig,
    district_map_df,
    geo_dict,
    district_geo_dict,
    geo_json_dict,
    df_nfhs_345,
    ind_dom_dist_options,
    nfhs_dist_ind_df,
    district_state_match,
    dist_state_kpi_df,
    aspir_dist_df,
)

register_page(__name__, path="/district-gis", title="District GIS")

# dbc select: KPI district map --> All India or States
# restricted to States only (All India requires more resources to deploy)
dd_india_or_state = dbc.Select(
    id="india-or-state-dd",
    size="sm",
    options=state_options,
    value="All India",
    persistence=True,
    persistence_type="session",
    style={"fontSize": "12px"},
)

# dbc select: KPI map domain
dd_domain_map = dbc.Select(
    id="kpi-domain-map-dd",
    size="sm",
    options=ind_dom_dist_options,
    value=ind_dom_dist_options[0]["value"],
    persistence=True,
    persistence_type="session",
    style={"fontSize": "12px"},
)

# dbc select: KPI district map
dd_kpi_map_district = dbc.Select(
    id="kpi-district-map-dd",
    size="sm",
    persistence=True,
    persistence_type="session",
    style={"fontSize": "12px"},
)

# %%
# dbc ButtonGroup with RadioItems
button_group_change = html.Div(
    [
        dbc.RadioItems(
            id="radios-change",
            className="btn-group",
            inputClassName="btn-check",
            labelClassName="btn btn-outline-info",
            labelCheckedClassName="active",
            options=[
                {"label": "NFHS-5", "value": "value"},
                {"label": "Change (2016-21)", "value": "Abs_Change"},
            ],
            value="value",
            persistence=True,
            persistence_type="session",
        ),
    ],
    className="radio-group",
)

# %%
# dbc button: download datatable
bt_dwd = dbc.Button(
    html.P(
        ["Download Table in ", html.Code("csv")],
        style={
            "margin-top": "12px",
            "fontWeight": "bold",
        },
    ),
    id="btn-dwd",
    class_name="me-1",
    outline=True,
    color="info",
)

# %%
# function to return indicator options by domain (sets a value)
@callback(
    Output("kpi-district-map-dd", "options"),
    Output("kpi-district-map-dd", "value"),
    Input("kpi-domain-map-dd", "value"),
)
# update dropdown options: indicator district based on indicator type
def update_district_kpi_options(indicator_domain):

    # dbc dropdown allows one selection
    district_kpis = sorted(
        nfhs_dist_ind_df.query("ind_domain == @indicator_domain").district_kpi.values,
        key=str.lower,
    )
    return [{"label": l, "value": l} for l in district_kpis], district_kpis[0]


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


# dbc district kpi map row
layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select All India or a State",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_india_or_state,
                        ]
                    ),
                    width=2,
                ),
                dbc.Col(
                    html.Div(
                        [
                            html.P(
                                "Select Indicator Domain",
                                style={
                                    "fontWeight": "bold",  # 'normal', #
                                    "textAlign": "left",  # 'center', #
                                    # 'paddingTop': '25px',
                                    "color": "DeepSkyBlue",
                                    "fontSize": "14px",
                                    "marginBottom": "10px",
                                },
                            ),
                            dd_domain_map,
                        ]
                    ),
                    width=3,
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
                            dd_kpi_map_district,
                        ]
                    ),
                    width=7,
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
                            button_group_change,
                            dcc.Graph(id="district-or-state-plot", figure=label_no_fig),
                        ]
                    ),
                    width=10,
                ),
            ],
            justify="start",
            align="center",
            # style={"paddingTop": "20px"},
        ),
        dbc.Row(
            [
                dbc.Col(create_card(card_num=1), width="auto"),
                dbc.Col(
                    [bt_dwd, dcc.Download(id="table-dwd")],
                    width="auto",
                    style={
                        "paddingLeft": "50px",
                    },
                ),
            ],
            justify="center",
            align="center",
        ),
        dbc.Row(
            dbc.Col(
                html.Div(
                    id="table-div", style={"maxHeight": "550px", "overflowY": "scroll"}
                ),
                id="table-col",
                width="auto",
            ),
            justify="evenly",
            align="center",
            style={"paddingTop": "30px", "paddingBottom": "30px"},
        ),
        # hidden div: share data table in Dash
        html.Div(id="table-df", style={"display": "none"}),
        # hidden div: share data table in Dash
        html.Div(id="ind-dmn", style={"display": "none"}),
        # hidden div: share data table in Dash
        html.Div(id="ind-id", style={"display": "none"}),
    ],
    fluid=True,
    style={"paddingTop": "20px"},
)

# %%
# function to avoid figure display inline
def update_cm_fig(cm_fig):
    cm_fig.update_geos(fitbounds="locations", visible=False)
    cm_fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    cm_fig.update_coloraxes(colorbar_len=0.85, colorbar_x=0.78)
    cm_fig.update_traces(marker_line_color="Gainsboro", marker_line_width=0.5)
    return cm_fig


# customed px continous color scale: name
color_scale_name = "Rainbow"
color_names = eval(f"px.colors.sequential.{color_scale_name}")

# customed color scale with color for NaNs
color_nan = "Gray"
customed_color_nan = [
    [0, color_nan],
    [0.001, color_nan],
    [0.001, color_names[0]],
]
customed_color_rem = [
    [(i + 1) / (len(color_names) - 1), a_color]
    for i, a_color in enumerate(color_names[1:])
]
customed_color_scale = customed_color_nan + customed_color_rem


@callback(
    Output("district-or-state-plot", "figure"),
    Output("card-tit-1", "children"),
    Output("card-val-1", "children"),
    Output("table-div", "children"),
    Output("table-df", "children"),
    Output("ind-dmn", "children"),
    Output("ind-id", "children"),
    Input("india-or-state-dd", "value"),
    Input("kpi-district-map-dd", "value"),
    Input("radios-change", "value"),
    State("kpi-domain-map-dd", "value"),
)
# use dropdown values: update geo-json and indicator in map (district-wise)
def disp_in_district_map(india_or_state, distr_kpi, value_or_change, distr_dmn):

    # test if all_india
    if "All India" in india_or_state:
        display_df = district_map_df.query(
            "variable == @distr_kpi & Round == 'NFHS-5'"
        ).set_index(["State", "District name"])
        display_df_4 = district_map_df.query(
            "variable == @distr_kpi & Round == 'NFHS-4'"
        ).set_index(["State", "District name"])
        # do not filter geojson
        geofile = geo_json_dict
    else:
        # query dataframe
        display_df = district_map_df.query(
            "State == @india_or_state & variable == @distr_kpi & Round == 'NFHS-5'"
        ).set_index(["State", "District name"])
        display_df_4 = district_map_df.query(
            "State == @india_or_state & variable == @distr_kpi & Round == 'NFHS-4'"
        ).set_index(["State", "District name"])
        # filter geojson by state
        geofile = {}
        geofile["type"] = "FeatureCollection"
        geofile["features"] = geo_dict[india_or_state]

    # calculate change
    display_df["Abs_Change"] = display_df.value - display_df_4.value

    # query state data
    matched_state = district_state_match.get(india_or_state, india_or_state)
    matched_indicator = dist_state_kpi_df.query(
        "Dom_in_Dist == @distr_dmn & kpi_district == @distr_kpi"
    )
    card_val = (
        None
        if pd.isna(*matched_indicator.kpi_state)
        else df_nfhs_345.query(
            "State == @matched_state & `Indicator Type` == @matched_indicator.Dom_in_State.values[0] & Indicator == @matched_indicator.kpi_state.values[0] & NFHS == 'NFHS 5'"
        ).Total.values
    )

    # determine changes for dash table
    pcnt_scale = 1 if re.findall(r"(\bsurveyed|interviewed\b)", distr_kpi) else 100
    table_df = pd.concat(
        [
            display_df_4.value.rename("NFHS-4") / pcnt_scale,
            display_df.value.rename("NFHS-5") / pcnt_scale,
            display_df.Abs_Change.rename("Abs. Change") / pcnt_scale,
        ],
        axis=1,
    )
    table_df["Growth"] = table_df["Abs. Change"].apply(
        lambda x: "" if pd.isna(x) else ("📈" if x > 0 else "📉")
    )

    # min-max block kpis - before setting missing as negatives
    display_df["Note_NFHS5"] = np.nan
    display_df["Note_Change"] = np.nan

    # Hack aspirational districts selection
    if re.findall(r"(?i)(\baspirational|gavi|laqshya\b)", india_or_state):
        # districts in dataframe
        dist_in_df = [",".join(elem) for elem in display_df.index]
        # districts to display
        dist_2_disp = aspir_dist_df[aspir_dist_df[india_or_state]].index
        # districts to be dropped
        dist_2_drop = np.setdiff1d(dist_in_df, dist_2_disp)
        # districts to be added (not reported)
        dist_2_add = np.setdiff1d(dist_2_disp, dist_in_df)
        # drop in dataframe
        display_df.drop(
            index=[(a_tup.split(",")[0], a_tup.split(",")[1]) for a_tup in dist_2_drop],
            inplace=True,
        )
        # set the range before adding the NA values (-1000)
        full_range = [
            display_df[value_or_change].min() - 0.5,
            display_df[value_or_change].max(),
        ]
        display_df.loc[display_df.value.notna(), "Note_NFHS5"] = "Value Reported"
        display_df.loc[
            display_df.value.isnull(), "Note_NFHS5"
        ] = "Value NOT Reported: (-1000)"
        display_df.loc[display_df.value.isnull(), "value"] = -1000
        display_df.loc[display_df.Abs_Change.notna(), "Note_Change"] = "Value Reported"
        display_df.loc[
            display_df.Abs_Change.isnull(), "Note_Change"
        ] = "Value NOT Reported: (-1000)"
        display_df.loc[display_df.Abs_Change.isnull(), "Abs_Change"] = -1000
        # now add the non-reported
        for a_tup in dist_2_add:
            # add the geo name for these guys
            display_df.loc[
                (a_tup.split(",")[0], a_tup.split(",")[1]), "District_geo"
            ] = (
                district_geo_dict.get(india_or_state, district_geo_dict["All India"])
                .query(
                    "State == @a_tup.split(',')[0] & `District name` == @a_tup.split(',')[1]"
                )
                .District_geo.values[0]
            )
            display_df.loc[
                (a_tup.split(",")[0], a_tup.split(",")[1]), value_or_change
            ] = -1000
            note_col = "Note_NFHS5" if value_or_change == "value" else "Note_Change"
            display_df.loc[
                (a_tup.split(",")[0], a_tup.split(",")[1]), note_col
            ] = "Value NOT Reported: (-1000)"

        # delete the non-aspirationals from data-table
        table_df.drop(
            index=[(a_tup.split(",")[0], a_tup.split(",")[1]) for a_tup in dist_2_drop],
            inplace=True,
        )
    else:
        # set the range before adding the NA values (-1000)
        full_range = [
            display_df[value_or_change].min() - 0.5,
            display_df[value_or_change].max(),
        ]
        display_df.loc[display_df.value.notna(), "Note_NFHS5"] = "Value Reported"
        display_df.loc[
            display_df.value.isnull(), "Note_NFHS5"
        ] = "Value NOT Reported: (-1000)"
        display_df.loc[display_df.value.isnull(), "value"] = -1000
        display_df.loc[display_df.Abs_Change.notna(), "Note_Change"] = "Value Reported"
        display_df.loc[
            display_df.Abs_Change.isnull(), "Note_Change"
        ] = "Value NOT Reported: (-1000)"
        display_df.loc[display_df.Abs_Change.isnull(), "Abs_Change"] = -1000

    display_df.reset_index(inplace=True)
    # set missing reporting districts (or not selected)
    not_reported_geo = np.setdiff1d(
        district_geo_dict.get(india_or_state, district_geo_dict["All India"])[
            "District_geo"
        ].values,
        display_df.query(f"{value_or_change}.notna()")["District_geo"].values,
    )
    # not_reported_geo = [
    #     district_geo_dict.get(india_or_state, district_geo_dict["All India"])
    #     .query("`District_geo` == @a_name")
    #     .District_geo.values[0]
    #     for a_name in not_reported
    # ]
    # concat not_reported as negatives
    display_df = (
        pd.concat(
            [
                display_df,
                pd.DataFrame(
                    {
                        "District_geo": not_reported_geo,
                        # "District_name": not_reported,
                        "Note_NFHS5"
                        if value_or_change == "value"
                        else "Note_Change": [
                            "District NOT in Selection: (-500)"
                            if re.findall(
                                r"(?i)(\baspirational|gavi|laqshya\b)", india_or_state
                            )
                            else "Value NOT Reported: (-1000)"
                        ]
                        * len(not_reported_geo),
                    }
                ),
            ],
            ignore_index=True,
        )
        .drop_duplicates(subset=["District_geo"], ignore_index=True)
        .fillna(
            {
                value_or_change: -500
                if re.findall(r"(?i)(\baspirational|gavi|laqshya\b)", india_or_state)
                else -1000
            }
        )
    )

    # district map
    cmap_fig = px.choropleth(
        display_df,
        geojson=geofile,
        featureidkey="properties.707_dist_7",  # 'properties.ST_NM', #
        locations="District_geo",
        color=value_or_change,
        labels={
            "District_geo": "District, State",
            "value": "NFHS-5 Value",
            "Abs_Change": "NFHS (5-4) Change",
            "Note_NFHS5": "Note",
            "Note_Change": "Note",
        },
        hover_data=["Note_NFHS5" if value_or_change == "value" else "Note_Change"],
        # color_continuous_scale = "RdBu",
        color_continuous_scale=customed_color_scale,
        range_color=full_range,
        # color_discrete_map={'red':'red', 'orange':'orange', 'green':'green'},
        # hover_data=[dd_value],
        projection="mercator",
        height=550,
    )

    table_df.reset_index(inplace=True)
    # there are NA values for NFHS 5 and 4 in table_df
    table_df.dropna(subset=["NFHS-4", "NFHS-5"], how="all", inplace=True)
    table_df.rename(columns={"District name": "District"}, inplace=True)
    # address numeric format data table
    num_format = (
        FormatTemplate.money(0)
        if "Rs." in distr_kpi
        else (
            Format.Format()
            if re.findall(r"(\bsurveyed|interviewed\b)", distr_kpi)
            else FormatTemplate.percentage(0)
        )
    )
    table_col_format = [
        {"name": i, "id": i}
        if i in ["State", "District"]
        else {
            "name": i,
            "id": i,
            "type": "numeric",
            "format": num_format,
        }
        for i in table_df.columns
    ]

    return (
        update_cm_fig(cmap_fig),
        f"NFHS-5 (2019-21) Average: {matched_state}",
        f"{str(card_val[0] if card_val else 'N/A')}",
        DataTable(
            data=table_df.to_dict("records"),
            columns=table_col_format,
        ),
        # csv to json: sharing data within Dash
        table_df[[col for col in table_df.columns if col != "Growth"]].to_json(
            orient="split"
        ),
        # share indicator domain
        distr_dmn,
        # share indicator name
        distr_kpi,
    )


# %%

# helper function for closing temporary files - stackoverflow
def close_tmp_file(tf):
    try:
        os.unlink(tf.name)
        tf.close()
    except:
        pass


# callback download conversion
@callback(
    Output("table-dwd", "data"),
    Input("btn-dwd", "n_clicks"),
    State("table-df", "children"),
    State("ind-dmn", "children"),
    State("ind-id", "children"),
    prevent_initial_call=True,
)
def download_table(_, df_table, ind_dom, ind_name):
    if not df_table:
        return None
    else:
        df = pd.read_json(df_table, orient="split")
        df["Domain"] = ind_dom
        df["Indicator"] = ind_name
        df_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        df_temp_file.flush()
        df.to_csv(
            df_temp_file.name,
            index=False,
            encoding="utf-8-sig",
            quoting=csv.QUOTE_NONNUMERIC,
        )

        # try with zip
        zip_tf = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        zf = ZipFile(zip_tf, mode="w")
        zf.write(df_temp_file.name, "NFHS_4_5_table.csv")

        # close uploaded temporary files
        zf.close()
        zip_tf.flush()
        zip_tf.seek(0)
        close_tmp_file(df_temp_file.name)
        close_tmp_file(zip_tf.name)

        return (
            # use instead dcc.send_file (with zip --> temp direct not working)
            dcc.send_file(zip_tf.name, filename="NFHS_4_5_table.zip")
        )
