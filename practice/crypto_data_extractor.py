import ccxt
import pandas as pd
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

# ========================
# 參數設定
# ========================
exchange = ccxt.binance({"rateLimit": 1200, "enableRateLimit": True})

symbols = [
    "BTC/USDT",
    "ETH/USDT",
    "BNB/USDT",
    "SOL/USDT",
    "XRP/USDT",
    "ADA/USDT",
    "AVAX/USDT",
    "LINK/USDT",
    "DOT/USDT",
    "TRX/USDT",
]

timeframe = "1h"
limit = 1500
start_date = "2020-10-13T00:00:00Z"
since = exchange.parse8601(start_date)


# ========================
# 抓資料函式
# ========================
def fetch_historical_data(
    symbol, timeframe, since, limit, max_loops=100, sleep_sec=0.5
):
    all_data = []
    loops = 0

    while loops < max_loops:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            if not ohlcv:
                break

            last_timestamp = ohlcv[-1][0]
            if last_timestamp <= since:
                break

            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            df = df[["close"]]
            df.columns = [symbol.replace("/", "")]
            all_data.append(df)

            since = last_timestamp + 1
            loops += 1
            time.sleep(sleep_sec)
        except Exception as e:
            tqdm.write(f"[❌] 抓取 {symbol} 發生錯誤：{e}")
            break

    return symbol, pd.concat(all_data) if all_data else pd.DataFrame()


# ========================
# 主程式
# ========================
def main():
    print(f"📊 開始提取歷史數據：{timeframe} 從 {start_date}")
    results = {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(
                fetch_historical_data, symbol, timeframe, since, limit
            ): symbol
            for symbol in symbols
        }

        # 用 tqdm 包住 as_completed，顯示「完成的幣種」數量
        for future in tqdm(
            as_completed(futures), total=len(symbols), desc="提取進度", unit="幣種"
        ):
            symbol = futures[future]
            try:
                symbol, df = future.result()
                if not df.empty:
                    results[symbol] = df
                    tqdm.write(f"✅ {symbol} 完成，共 {len(df)} 筆")
                else:
                    tqdm.write(f"[⚠️] {symbol} 無資料")
            except Exception as e:
                tqdm.write(f"[❌] {symbol} 發生錯誤：{e}")

    if results:
        price_df = pd.concat(results.values(), axis=1)
        price_df.dropna(inplace=True)
        price_df.to_csv("crypto_historical_data.csv")
        print("📁 已儲存到 crypto_historical_data.csv")
    else:
        print("[❌] 沒有成功抓取的資料")


# ========================
# 執行
# ========================
if __name__ == "__main__":
    main()
