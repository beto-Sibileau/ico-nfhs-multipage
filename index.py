# %%
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output

# %%
# Connect to main app.py file
from app import app, server

# %%
# Connect to your app pages
from pages import home, district_gis  # , district_scatter, state_trend, state_equity

# %%
# app shared layout (title and home directory)


# %%
# display content using urls
@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def display_page(pathname):
    match pathname:
        case "/apps/home":
            return home.layout
        case "/apps/district_gis":
            return district_gis.layout
        case "/apps/district_scatter":
            return district_scatter.layout
        case "/apps/state_trend":
            return state_trend.layout
        case "/apps/state_equity":
            return state_equity.layout
        case _:
            return home.layout


# actual page content
dcc.Loading(
    children=html.Div(
        id="page-content",
        children=[],
        style={
            "paddingTop": "20px",
        },
    ),
    id="loading-page-content",
    type="circle",
    fullscreen=True,
),
