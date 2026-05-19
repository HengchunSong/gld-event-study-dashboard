from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
WEB_DIR = ROOT / "web"
SOURCE_URL = "https://stooq.com/q/d/l/?s=gld.us&i=d"
YAHOO_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/GLD?period1=1095379200&period2={period2}&interval=1d&events=history"


def download_gld() -> pd.DataFrame:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    request = Request(SOURCE_URL, headers={"User-Agent": "Mozilla/5.0 quantde-demo"})
    with urlopen(request, timeout=30) as response:
        csv_text = response.read().decode("utf-8")

    csv_path = DATA_DIR / "gld_daily.csv"
    csv_path.write_text(csv_text, encoding="utf-8")
    if csv_text.startswith("Date,"):
        df = pd.read_csv(csv_path)
        df.attrs["source_url"] = SOURCE_URL
        return df

    df = download_gld_from_yahoo()
    df.to_csv(csv_path, index=False)
    return df


def download_gld_from_yahoo() -> pd.DataFrame:
    url = YAHOO_CHART_URL.format(period2=int(time.time()))
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 quantde-demo"})
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    result = payload["chart"]["result"][0]
    timestamps = result["timestamp"]
    quote = result["indicators"]["quote"][0]
    adjusted = result["indicators"].get("adjclose", [{}])[0].get("adjclose", quote["close"])
    rows = []
    for i, timestamp in enumerate(timestamps):
        if quote["close"][i] is None:
            continue
        rows.append(
            {
                "Date": pd.to_datetime(timestamp, unit="s", utc=True).strftime("%Y-%m-%d"),
                "Open": quote["open"][i],
                "High": quote["high"][i],
                "Low": quote["low"][i],
                "Close": adjusted[i] if adjusted[i] is not None else quote["close"][i],
                "Volume": quote["volume"][i],
            }
        )
    df = pd.DataFrame(rows)
    df.attrs["source_url"] = url
    return df


def prepare_records(raw: pd.DataFrame) -> list[dict[str, object]]:
    df = raw.rename(columns=str.lower).copy()
    expected = {"date", "open", "high", "low", "close", "volume"}
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Missing columns from source data: {sorted(missing)}")

    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").drop_duplicates("date", keep="last")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close", "volume"])

    df["return_1d"] = df["close"].pct_change()
    df["drawdown_5d"] = df["close"] / df["close"].shift(5) - 1
    df["forward_return_3d"] = df["close"].shift(-3) / df["close"] - 1
    df["dollar_volume"] = df["close"] * df["volume"]
    df["volume_zscore_20d"] = (df["volume"] - df["volume"].rolling(20).mean()) / df["volume"].rolling(20).std()

    df = df.replace({np.nan: None})
    records = []
    for row in df.itertuples(index=False):
        records.append(
            {
                "date": row.date.strftime("%Y-%m-%d"),
                "open": round(float(row.open), 4),
                "high": round(float(row.high), 4),
                "low": round(float(row.low), 4),
                "close": round(float(row.close), 4),
                "volume": int(row.volume),
                "return_1d": _round_optional(row.return_1d),
                "drawdown_5d": _round_optional(row.drawdown_5d),
                "forward_return_3d": _round_optional(row.forward_return_3d),
                "dollar_volume": _round_optional(row.dollar_volume, 2),
                "volume_zscore_20d": _round_optional(row.volume_zscore_20d),
            }
        )
    return records


def _round_optional(value: object, digits: int = 8) -> float | None:
    if value is None or pd.isna(value):
        return None
    return round(float(value), digits)


def build_html(records: list[dict[str, object]], source_url: str = SOURCE_URL) -> str:
    data_json = json.dumps(
        {
            "symbol": "GLD",
            "source": source_url,
            "generated_at": pd.Timestamp.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            "records": records,
        },
        separators=(",", ":"),
    )
    template = (ROOT / "templates" / "dashboard.html").read_text(encoding="utf-8")
    return template.replace("__EMBEDDED_GLD_JSON__", data_json)


def main() -> None:
    WEB_DIR.mkdir(parents=True, exist_ok=True)
    raw = download_gld()
    records = prepare_records(raw)
    html = build_html(records, raw.attrs.get("source_url", SOURCE_URL))
    (WEB_DIR / "index.html").write_text(html, encoding="utf-8")
    first = records[0]["date"] if records else "n/a"
    last = records[-1]["date"] if records else "n/a"
    print(f"Wrote {WEB_DIR / 'index.html'}")
    print(f"Embedded {len(records)} GLD daily records from {first} to {last}")


if __name__ == "__main__":
    main()
