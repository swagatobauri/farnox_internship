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

# FastAPI application ka main instance banate hain
app = FastAPI(
    title="Stock Dashboard API",
    description="API for stock market data",
    version="1.0.0"
)

# HTML/CSS/JS files ko frontend par serve karne ke liye route set kiya
app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)
    print("Created data folder.")

# Default home page load karne ke liye route
@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)

# Kisi specific company ka stock data fetch karne wala route
@app.get("/stock/{ticker}")
def get_stock_data(ticker: str, period: str = "1mo"):
    try:
        ticker = ticker.upper()
        # Yahoo Finance se data layein
        stock = yf.Ticker(ticker)
        history = stock.history(period=period)

        if history.empty:
            return JSONResponse(
                status_code=404,
                content={"error": "Data not found for " + ticker}
            )

        info = stock.info

        company_name = info.get("longName", ticker)
        current_price = info.get("currentPrice", info.get("regularMarketPrice", 0))
        market_cap = info.get("marketCap", 0)
        sector = info.get("sector", "N/A")
        currency = info.get("currency", "USD")

        # Dates ko string format mein fix karte hain Plotly chart ke liye
        date_strs = history.index.strftime("%Y-%m-%d").tolist()

        # Ek naya Candlestick chart banate hain
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
            title=company_name + " (" + ticker + ") — Stock Price",
            xaxis_title="Date",
            yaxis_title="Price (" + currency + ")",
            xaxis_type="date",
            xaxis_rangeslider_visible=False,
        )

        chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # Downloaded data ko backup ke zarurat ke hisab se CSV mein save karein
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
            content={"error": "An error occurred: " + str(e)}
        )

# Multiple stocks ek saath compare karne ka route (optional function)
@app.get("/compare")
def compare_stocks(tickers: str = "AAPL,GOOGL,MSFT", period: str = "1mo"):
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        fig = go.Figure()

        for ticker in ticker_list:
            stock = yf.Ticker(ticker)
            history = stock.history(period=period)

            if not history.empty:
                # Prices ko compare karne ke liye 100 pe normalize karte hain
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
            content={"error": "An error occurred: " + str(e)}
        )

# Quick suggestion list UI ko populate karne ke liye
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
