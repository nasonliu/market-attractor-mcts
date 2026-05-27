from __future__ import annotations

from pathlib import Path
import time

import pandas as pd
import yfinance as yf


def download_prices(config: dict, data_dir: Path, force: bool = False) -> pd.DataFrame:
    output_path = data_dir / "prices.csv"
    if output_path.exists() and not force:
        return pd.read_csv(output_path, index_col=0, parse_dates=True)

    tickers = config["data"]["tickers"]
    prices = _download_tickers_sequentially(config, tickers)
    prices = prices.sort_index().ffill().dropna(how="all")
    missing = [ticker for ticker in tickers if ticker not in prices.columns or prices[ticker].dropna().empty]
    if missing:
        raise RuntimeError(f"Missing downloaded price data for: {missing}")
    prices.to_csv(output_path)
    return prices


def _download_tickers_sequentially(config: dict, tickers: list[str]) -> pd.DataFrame:
    closes = {}
    for ticker in tickers:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                raw = yf.download(
                    tickers=ticker,
                    start=config["data"]["start_date"],
                    end=config["data"].get("end_date"),
                    auto_adjust=True,
                    progress=False,
                    threads=False,
                )
                close = _extract_single_close(raw, ticker)
                if not close.dropna().empty:
                    closes[ticker] = close
                    break
            except Exception as exc:
                last_error = exc
            time.sleep(1.5 * (attempt + 1))
        else:
            raise RuntimeError(f"Failed to download {ticker}") from last_error

    return pd.DataFrame(closes)


def _extract_single_close(raw: pd.DataFrame, ticker: str) -> pd.Series:
    if isinstance(raw.columns, pd.MultiIndex):
        if (ticker, "Close") in raw.columns:
            return raw[(ticker, "Close")].rename(ticker)
        if ("Close", ticker) in raw.columns:
            return raw[("Close", ticker)].rename(ticker)
    if "Close" in raw.columns:
        return raw["Close"].rename(ticker)
    raise ValueError(f"Unable to extract close prices for {ticker}.")


def _extract_close_prices(raw: pd.DataFrame, tickers: list[str]) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        closes = {}
        for ticker in tickers:
            if (ticker, "Close") in raw.columns:
                closes[ticker] = raw[(ticker, "Close")]
            elif ("Close", ticker) in raw.columns:
                closes[ticker] = raw[("Close", ticker)]
        return pd.DataFrame(closes)

    if "Close" in raw.columns and len(tickers) == 1:
        return raw[["Close"]].rename(columns={"Close": tickers[0]})

    raise ValueError("Unable to extract close prices from yfinance response.")
