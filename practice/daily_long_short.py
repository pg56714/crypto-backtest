# ========================
# 📊 當天多空前四名資產輸出
# ========================

import pandas as pd
import numpy as np
import quantstats_lumi as qs
import os

# ========================
# 參數設定
# ========================
file_path = "crypto_historical_data.csv"  # 歷史數據檔案
output_path = "backtest_results"  # 儲存績效報告的資料夾
timeframe = 12  # 每個時間單位為12小時
fraction = 0.0005  # 交易成本
daily_output_file = os.path.join(output_path, "daily_long_short.csv")  # 當天結果檔案

# 確保輸出目錄存在
os.makedirs(output_path, exist_ok=True)


# ========================
# 讀取價格資料
# ========================
print("📊 正在讀取歷史價格資料...")
price_df = pd.read_csv(file_path, index_col=0, parse_dates=True)
price_df = price_df.resample(f"{timeframe}h").last()
price_df.dropna(inplace=True)


# ========================
# 策略邏輯
# ========================
def generate_returns(data, param):
    data_ret = data.pct_change().dropna()
    method_result = (
        (data_ret.rolling(param).sum()).rank(axis=1, ascending=False).dropna()
    )

    def transform_position(value):
        if value <= 4:
            return 1
        elif value >= len(data.columns) - 3:
            return -1
        else:
            return 0

    positions = method_result.map(transform_position)
    positions /= 8  # 等權重分配

    ret = data_ret * positions.shift(1) - fraction * np.abs(
        positions - positions.shift(1)
    )
    ret.dropna(inplace=True)
    ret["returns"] = ret.sum(axis=1)
    return ret, positions


# ========================
# 調整參數 (Tuning Parameters)
# ========================
print("⚙️ 正在調整策略參數...")
results = []

for param in range(10, 200):
    returns, positions = generate_returns(price_df, param)
    sharpe = qs.stats.sharpe(returns["returns"], periods=365 * 24 / timeframe)
    results.append([param, sharpe])

results_df = pd.DataFrame(results, columns=["period", "sharpe"])
best_param = results_df.sort_values("sharpe", ascending=False).iloc[0]["period"]
print(f"🏆 最佳參數: period = {best_param}")


# ========================
# 當天多空前四名資產計算
# ========================
print("📊 正在計算當天的多空前四名資產...")

# 確保有足夠的資料
latest_data = price_df.iloc[-(int(best_param) + 1) :].copy()
print(f"✅ 最新數據行數: {len(latest_data)}，所需行數: {int(best_param)+1}")
if len(latest_data) < int(best_param) + 1:
    raise ValueError("❌ 最新數據不足，請確保至少有 param + 1 個時間點的資料。")

# 計算滾動收益率排名
latest_ret = latest_data.pct_change().dropna()
method_result = (
    (latest_ret.rolling(int(best_param)).sum()).rank(axis=1, ascending=False).dropna()
)

# 檢查 method_result 是否有資料
if method_result.empty:
    raise ValueError("❌ method_result 為空，請檢查資料輸入或調整 param 值。")

# 獲取最新一個時間點的排名結果
latest_rank = method_result.iloc[-1].sort_values(ascending=False)

# 提取多頭和空頭前四名
top4_long = latest_rank.head(4).index.tolist()
bottom4_short = latest_rank.tail(4).index.tolist()

# 建立 DataFrame 儲存結果
daily_results = pd.DataFrame(
    {
        "Asset": top4_long + bottom4_short,
        "Rank": list(range(1, 5))
        + list(range(len(latest_rank) - 3, len(latest_rank) + 1)),
        "Signal": ["Long"] * 4 + ["Short"] * 4,
    }
)

# 儲存結果至 CSV 檔案
daily_results.to_csv(daily_output_file, index=False)
print(f"✅ 當天多空前四名資產結果已保存至: {daily_output_file}")

# 顯示結果在終端機上
print("\n🔍 📈 **多頭前四名資產 (Long Top 4):**")
for asset in top4_long:
    print(f"✅ {asset}")

print("\n🔍 📉 **空頭後四名資產 (Short Bottom 4):**")
for asset in bottom4_short:
    print(f"❌ {asset}")

print("🚀 當天多空前四名計算與輸出完成！")
