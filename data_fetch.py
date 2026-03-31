import os
import yfinance as yf
import pandas as pd
from datetime import datetime

# Yahan par apni companies aur unke tickers define karein
TICKERS = {
    "INFY.NS":      "Infosys",
    "TCS.NS":       "Tata Consultancy Services",
    "RELIANCE.NS":  "Reliance Industries",
    "HDFCBANK.NS":  "HDFC Bank",
    "WIPRO.NS":     "Wipro",
}

PERIOD = "1y"
INTERVAL = "1d"
OUTPUT_FOLDER = "data"

# Data folder create karo agar nahi hai
if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print("Data fetch shuru hua...")

for ticker, company_name in TICKERS.items():
    print("Processing", company_name)

    # Yahoo finance se data download karte hain
    raw_df = yf.download(
        ticker,
        period=PERIOD,
        interval=INTERVAL,
        auto_adjust=True,
        progress=False,
    )

    if raw_df.empty:
        print("Warning: Koi data nahi mila", ticker, "ke liye")
        continue

    # Agar MultiIndex columns aayein toh unhe clean karein
    if isinstance(raw_df.columns, pd.MultiIndex):
        raw_df.columns = raw_df.columns.droplevel(1)

    df = raw_df.copy()
    df.index.name = "Date"
    df = df.reset_index()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    # Naye columns jaise Returns aur Moving Average calculate karte hain
    df["Daily_Return"] = ((df["Close"] - df["Open"]) / df["Open"]).round(4)
    df["MA_7"] = df["Close"].rolling(window=7).mean().round(2)
    df["High_52W"] = df["High"].rolling(window=252, min_periods=1).max().round(2)
    df["Low_52W"] = df["Low"].rolling(window=252, min_periods=1).min().round(2)

    last = df.iloc[-1]
    
    print("Summary for", company_name)
    print("Total rows:", df.shape[0])
    print("Latest Close:", last['Close'])

    # CSV file save karein
    file_name = ticker + "_" + PERIOD + ".csv"
    file_path = os.path.join(OUTPUT_FOLDER, file_name)
    df.to_csv(file_path, index=False)
    
    print("Saved file in", file_path)

print("Data fetching pura ho gaya.")
