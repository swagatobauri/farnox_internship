import os
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go
import plotly.utils
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

app = FastAPI(
    title="Stock Dashboard API",
    description="API for stock market data",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)
    print(f"Created '{DATA_FOLDER}' folder.")

@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

@app.get("/stock/{ticker}")
def get_stock_data(ticker: str, period: str = "1mo"):
    try:
        ticker = ticker.upper()
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)

        if history.empty:
            return JSONResponse(
                status_code=404,
                content={"error": f"Data for '{ticker}' not found."}
            )

        info = stock.info

        company_name = info.get("longName", ticker)
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        market_cap = info.get("marketCap", 0)
        sector = info.get("sector", "N/A")
        currency = info.get("currency", "USD")

        date_strs = history.index.strftime("%Y-%m-%d").tolist()

        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=date_strs,
                    open=history["Open"].tolist(),
                    high=history["High"].tolist(),
                    low=history["Low"].tolist(),
                    close=history["Close"].tolist(),
                    name=ticker,
                    increasing_line_color="#16a34a",
                    decreasing_line_color="#dc2626",
                )
            ]
        )

        fig.update_layout(
            title=f"{company_name} ({ticker}) — Stock Price",
            xaxis_title="Date",
            yaxis_title=f"Price ({currency})",
            xaxis_type="date",
            xaxis_rangeslider_visible=False,
        )

        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        file_path = os.path.join(DATA_FOLDER, f"{ticker}_data.csv")
        history.to_csv(file_path)

        return {
            "ticker": ticker,
            "company_name": company_name,
            "current_price": round(current_price, 2),
            "market_cap": market_cap,
            "sector": sector,
            "currency": currency,
            "period": period,
            "data_points": len(history),
            "chart": chart_json,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred: {str(e)}"}
        )

@app.get("/compare")
def compare_stocks(tickers: str = "AAPL,GOOGL,MSFT", period: str = "1mo"):
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        fig = go.Figure()

        for ticker in ticker_list:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)

            if not history.empty:
                normalized = (history["Close"] / history["Close"].iloc[0]) * 100

                fig.add_trace(
                    go.Scatter(
                        x=history.index,
                        y=normalized,
                        mode="lines",
                        name=ticker,
                        line=dict(width=2)
                    )
                )

        fig.update_layout(
            title="Stock Comparison (Normalized to 100)",
            xaxis_title="Date",
            yaxis_title="Normalized Price",
            template="plotly_dark",
            paper_bgcolor="#1a1a2e",
            plot_bgcolor="#16213e",
            font=dict(color="#e0e0e0"),
        )

        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return {
            "tickers": ticker_list,
            "period": period,
            "chart": chart_json
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"An error occurred: {str(e)}"}
        )

@app.get("/popular-stocks")
def popular_stocks():
    return {
        "indian_stocks": [
            {"ticker": "TCS.NS",       "name": "Tata Consultancy Services"},
            {"ticker": "RELIANCE.NS",  "name": "Reliance Industries"},
            {"ticker": "INFY.NS",      "name": "Infosys"},
            {"ticker": "HDFCBANK.NS",  "name": "HDFC Bank"},
            {"ticker": "WIPRO.NS",     "name": "Wipro"},
        ],
        "us_stocks": [
            {"ticker": "AAPL",  "name": "Apple Inc."},
            {"ticker": "GOOGL", "name": "Alphabet (Google)"},
            {"ticker": "MSFT",  "name": "Microsoft"},
            {"ticker": "AMZN",  "name": "Amazon"},
            {"ticker": "TSLA",  "name": "Tesla"},
        ]
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
