import ccxt
import pandas as pd

exchange = ccxt.binance()

data = exchange.fetch_ohlcv("BTC/USDT", "1m")

col_name = ["timestamp", "open", "high", "low", "close", "volume"]
df = pd.DataFrame(data, columns=col_name)
df.set_index("timestamp", inplace=True)
print(df)
