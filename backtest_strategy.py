######################### 前置作業 #########################
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

# 確保輸出目錄存在
os.makedirs(output_path, exist_ok=True)

# ========================
# 讀取價格資料
# ========================
print("📊 正在讀取歷史價格資料...")
price_df = pd.read_csv(file_path, index_col=0, parse_dates=True)
price_df = price_df.resample(f"{timeframe}h").last()
price_df.dropna(inplace=True)

# 切分訓練跟測試的資料比例
total_rows = len(price_df)
split_index = int(total_rows * 0.75)
training = price_df.copy().iloc[:split_index]
testing = price_df.copy().iloc[split_index:]

print(f"✅ 訓練集範圍: {training.index[0]} → {training.index[-1]}")
print(f"✅ 測試集範圍: {testing.index[0]} → {testing.index[-1]}")


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

    # 等權重分配
    positions /= 8

    ret = data_ret * positions.shift(1) - fraction * np.abs(
        positions - positions.shift(1)
    )
    ret.dropna(inplace=True)
    ret["returns"] = ret.sum(axis=1)
    return ret, positions


# ========================
# 調整參數 (Tuning Parameters)
# ========================
results = []

print("⚙️ 正在調整策略參數...")
for param in range(10, 200):
    returns, positions = generate_returns(training, param)
    sharpe = qs.stats.sharpe(returns["returns"], periods=365 * 24 / timeframe)
    results.append([param, sharpe])

results_df = pd.DataFrame(results, columns=["period", "sharpe"])
best_param = results_df.sort_values("sharpe", ascending=False).iloc[0]["period"]
print(f"🏆 最佳參數: period = {best_param}")

# 儲存參數調整結果
results_df.to_csv(
    os.path.join(output_path, "parameter_tuning_results.csv"), index=False
)
print("✅ 參數調整結果已保存。")


# ========================
# 訓練集回測
# ========================
print("📈 訓練集回測中...")
returns_train, positions_train = generate_returns(training, int(best_param))
report_file_train = os.path.join(output_path, "training_report.html")
qs.reports.html(
    returns_train["returns"],
    output=report_file_train,
    title="Training Performance Report",
)
print(f"✅ 訓練集績效報告已生成: {report_file_train}")

# ========================
# 測試集回測
# ========================
print("📊 測試集回測中...")
returns_test, positions_test = generate_returns(testing, int(best_param))
report_file_test = os.path.join(output_path, "testing_report.html")
qs.reports.html(
    returns_test["returns"], output=report_file_test, title="Testing Performance Report"
)
print(f"✅ 測試集績效報告已生成: {report_file_test}")

# ========================
# 全資料回測
# ========================
print("📊 全資料回測中...")
returns_full, positions_full = generate_returns(price_df, int(best_param))
report_file_full = os.path.join(output_path, "full_report.html")
qs.reports.html(
    returns_full["returns"],
    output=report_file_full,
    title="Full Data Performance Report",
)
print(f"✅ 全資料績效報告已生成: {report_file_full}")

# ========================
# 顯示重要指標
# ========================
print("🔍 訓練集關鍵績效指標：")
print(
    f"📊 年化報酬率: {qs.stats.cagr(returns_train['returns'], periods=365*24/timeframe):.2%}"
)
print(f"📉 最大回撤: {qs.stats.max_drawdown(returns_train['returns']):.2%}")
print(
    f"📈 夏普比率: {qs.stats.sharpe(returns_train['returns'], periods=365*24/timeframe):.2f}"
)

print("🔍 測試集關鍵績效指標：")
print(
    f"📊 年化報酬率: {qs.stats.cagr(returns_test['returns'], periods=365*24/timeframe):.2%}"
)
print(f"📉 最大回撤: {qs.stats.max_drawdown(returns_test['returns']):.2%}")
print(
    f"📈 夏普比率: {qs.stats.sharpe(returns_test['returns'], periods=365*24/timeframe):.2f}"
)

print("🔍 全資料關鍵績效指標：")
print(
    f"📊 年化報酬率: {qs.stats.cagr(returns_full['returns'], periods=365*24/timeframe):.2%}"
)
print(f"📉 最大回撤: {qs.stats.max_drawdown(returns_full['returns']):.2%}")
print(
    f"📈 夏普比率: {qs.stats.sharpe(returns_full['returns'], periods=365*24/timeframe):.2f}"
)

print("🚀 回測完成！所有結果已保存至指定資料夾。")
