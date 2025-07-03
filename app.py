import dash
from dash import dcc, html
from datetime import datetime as dt
import yfinance as yf
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
from model import prediction  # Importing prediction model


# Function to generate stock price figure
def get_stock_price_fig(df):
    fig = px.line(df, x="Date", y=["Close", "Open"], title="Closing and Opening Price vs Date")
    return fig

# Function to generate indicators figure
def get_more(df):
    df["EWA_20"] = df["Close"].ewm(span=20, adjust=False).mean()
    fig = px.scatter(df, x="Date", y="EWA_20", title="Exponential Moving Average vs Date")
    fig.update_traces(mode="lines+markers")
    return fig

# Dash App Initialization
app = dash.Dash(__name__, external_stylesheets=["https://fonts.googleapis.com/css2?family=Roboto&display=swap"])
server = app.server

# Layout of the app
app.layout = html.Div(
    [
        html.Div(
            [
                html.P("Welcome to the Future Stock: Predictive Analysis App!    Build using Dash.", className="start"),
                html.Div([
                    html.P("Input stock code: "),
                    html.Div([
                        dcc.Input(id="dropdown_tickers", type="text"),
                        html.Button("Submit", id="submit"),
                    ], className="form")
                ], className="input-place"),
                html.Div([
                    dcc.DatePickerRange(
                        id="my-date-picker-range",
                        min_date_allowed=dt(1995, 8, 5),
                        max_date_allowed=dt.now(),
                        initial_visible_month=dt.now(),
                        end_date=dt.now().date(),
                    ),
                ], className="date"),
                html.Div([
                    html.Button("Stock Price", className="stock-btn", id="stock"),
                    html.Button("Indicators", className="indicators-btn", id="indicators"),
                    dcc.Input(id="n_days", type="text", placeholder="Number of days"),
                    html.Button("Forecast", className="forecast-btn", id="forecast"),
                ], className="buttons"),
            ],
            className="nav",
        ),

        html.Div(
            [
                html.Div([html.Img(id="logo"), html.P(id="ticker")], className="header"),
                html.Div(id="description", className="description_ticker"),
                html.Div([], id="graphs-content"),
                html.Div([], id="main-content"),
                html.Div([], id="forecast-content"),
            ],
            className="content",
        ),
    ],
    className="container",
)

# Callback for updating company information
@app.callback(
    [
        Output("description", "children"),
        Output("logo", "src"),
        Output("ticker", "children"),
        Output("stock", "n_clicks"),
        Output("indicators", "n_clicks"),
        Output("forecast", "n_clicks"),
    ],
    [Input("submit", "n_clicks")],
    [State("dropdown_tickers", "value")],
)
def update_data(n, val):
    if not n:
        return (
            # "Hey there! Please enter a legitimate stock code to get details.",
            html.P(
        "Hey there! Please enter a legitimate stock code to get details.",
        style={"font-size": "20px"}  
),
            "https://images.rawpixel.com/image_800/czNmcy1wcml2YXRlL3Jhd3BpeGVsX2ltYWdlcy93ZWJzaXRlX2NvbnRlbnQvbHIvay0xMC1hb20tMjA5MzUtb2xqMDQyMHdvcmQtMDUtc3RvY2ttZXJrZXQuanBn.jpg",  # Default logo
            "Future Stock",
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )

    if not val:
        raise PreventUpdate

    try:
        ticker = yf.Ticker(val)
        info = ticker.info



        # Get values safely with .get()
        long_summary = info.get("longBusinessSummary", "No description available.")
        logo_url = info.get("logo_url","")
        # df['logo'].values[0]
        short_name = info.get("shortName", val.upper())

        if not logo_url or not logo_url.startswith("http"):
            logo_url = "https://img.freepik.com/free-vector/stock-market-concept-design_1017-13713.jpg?semt=ais_hybrid"  # Fallback logo

        return long_summary, logo_url, short_name, dash.no_update, dash.no_update, dash.no_update

    except Exception as e:
        print(f"Error fetching stock data: {e}")
        return (
            "Error fetching stock details. Please check the stock code.",
            "https://via.placeholder.com/150",
            "Invalid Stock",
            dash.no_update,
            dash.no_update,
            dash.no_update,
        )



# Callback for stock price graph
@app.callback(
    [Output("graphs-content", "children")],
    [Input("stock", "n_clicks"), Input("my-date-picker-range", "start_date"), Input("my-date-picker-range", "end_date")],
    [State("dropdown_tickers", "value")],
)
def stock_price(n, start_date, end_date, val):
    if not n or not val:
        raise PreventUpdate

    df = yf.download(val, start=start_date, end=end_date)
    
    # Flatten multi-index columns (Fix for 'Date' column error)
    df.columns = df.columns.to_flat_index()
    df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    df.reset_index(inplace=True)
    fig = get_stock_price_fig(df)
    return [dcc.Graph(figure=fig)]

# Callback for indicators graph
@app.callback(
    [Output("main-content", "children")],
    [Input("indicators", "n_clicks"), Input("my-date-picker-range", "start_date"), Input("my-date-picker-range", "end_date")],
    [State("dropdown_tickers", "value")],
)
def indicators(n, start_date, end_date, val):
    if not n or not val:
        raise PreventUpdate

    df_more = yf.download(val, start=start_date, end=end_date)
    
    # Flatten multi-index columns
    df_more.columns = df_more.columns.to_flat_index()
    df_more.columns = [col[0] if isinstance(col, tuple) else col for col in df_more.columns]


    df_more.reset_index(inplace=True)
    fig = get_more(df_more)
    return [dcc.Graph(figure=fig)]

# Callback for forecast graph
@app.callback(
    [Output("forecast-content", "children")],
    [Input("forecast", "n_clicks")],
    [State("n_days", "value"), State("dropdown_tickers", "value")],
)
def forecast(n, n_days, val):
    if not n or not val:
        raise PreventUpdate

    try:
        fig = prediction(val, int(n_days) + 1)
        return [dcc.Graph(figure=fig)]
    except Exception as e:
        print(f"Error in forecast: {e}")
        return ["Forecasting error, please check input values."]

if __name__ == "__main__":
    app.run_server(debug=True)
    

