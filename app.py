from dash import Dash, dcc, get_asset_url, html, page_container, page_registry
import dash_bootstrap_components as dbc

# %%
fontawesome_stylesheet = "https://use.fontawesome.com/releases/v5.8.1/css/all.css"
# Build App
# meta_tags are required for the app layout to be mobile responsive
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, fontawesome_stylesheet],
    use_pages=True,
)

# title row
title_row = dbc.Container(
    dbc.Row(
        [
            dbc.Col(
                html.A(
                    [
                        html.Img(src=get_asset_url("logo-unicef-large.svg")),
                    ],
                    href=list(page_registry.values())[0]["relative_path"],
                ),
                width=3,
                # width={"size": 3, "offset": 1},
                style={"paddingLeft": "20px", "paddingTop": "20px"},
            ),
            dbc.Col(
                html.Div(
                    [
                        html.H6(
                            "National Family Health Survey",
                            style={
                                "fontWeight": "bold",
                                "textAlign": "center",
                                "paddingTop": "25px",
                                "color": "white",
                                "fontSize": "32px",
                            },
                        ),
                    ]
                ),
                # width='auto',
                width={"size": "auto", "offset": 1},
            ),
        ],
        justify="start",
        align="center",
    ),
    fluid=True,
)

# App Layout
app.layout = dbc.Container(
    [
        # title Div
        html.Div(
            [title_row],
            style={
                "height": "100px",
                "width": "100%",
                "backgroundColor": "DeepSkyBlue",
                "margin-left": "auto",
                "margin-right": "auto",
                "margin-top": "15px",
            },
        ),
        dcc.Loading(
            children=page_container,
            id="loading-map",
            type="circle",
            fullscreen=True,
        ),
    ],
    fluid=True,
)

# to deploy using WSGI server
server = app.server
# app tittle for web browser
app.title = "NFHS"

# %%
# Run app and print out the application URL
if __name__ == "__main__":
    app.run_server(debug=True)
