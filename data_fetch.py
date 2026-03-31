import os
import yfinance as yf
import pandas as pd
from datetime import datetime

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

if not os.path.exists(OUTPUT_FOLDER):
    os.makedirs(OUTPUT_FOLDER)

print("-" * 55)
print(f"Data fetch script started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total companies: {len(TICKERS)}")
print(f"Period: {PERIOD}  |  Interval: {INTERVAL}")
print("-" * 55)

for ticker, company_name in TICKERS.items():
    print(f"\nProcessing: {company_name} ({ticker})")

    raw_df = yf.download(
        ticker,
        period=PERIOD,
        interval=INTERVAL,
        auto_adjust=True,
        progress=False,
    )

    if raw_df.empty:
        print(f"  WARNING: No data found for {ticker}. Skipping.")
        continue

    if isinstance(raw_df.columns, pd.MultiIndex):
        raw_df.columns = raw_df.columns.droplevel(1)

    df = raw_df.copy()
    df.index.name = "Date"
    df = df.reset_index()

    df["Date"] = pd.to_datetime(df["Date"])
    df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

    df["Daily_Return"] = ((df["Close"] - df["Open"]) / df["Open"]).round(4)
    df["MA_7"] = df["Close"].rolling(window=7).mean().round(2)
    df["High_52W"] = df["High"].rolling(window=252, min_periods=1).max().round(2)
    df["Low_52W"] = df["Low"].rolling(window=252, min_periods=1).min().round(2)

    print(f"\n  --- {company_name} Summary ---")
    print(f"  Total rows  : {df.shape[0]}")
    print(f"  Total cols  : {df.shape[1]}")
    print(f"  Date range  : {df['Date'].iloc[0]}  to  {df['Date'].iloc[-1]}")

    last = df.iloc[-1]
    print(f"  Latest Close: {last['Close']:.2f}")
    print(f"  Latest MA_7 : {last['MA_7']:.2f}")
    print(f"  52W High    : {last['High_52W']:.2f}")
    print(f"  52W Low     : {last['Low_52W']:.2f}")
    print(f"  Daily Return: {last['Daily_Return']:.4f}  ({last['Daily_Return']*100:.2f}%)")

    file_name = f"{ticker}_{PERIOD}.csv"
    file_path = os.path.join(OUTPUT_FOLDER, file_name)
    df.to_csv(file_path, index=False)
    print(f"\n  Saved: {file_path}")
    print("-" * 55)

print(f"\nData fetching complete.")
print(f"CSV files are saved in: {os.path.abspath(OUTPUT_FOLDER)}/")
print(f"Script finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
