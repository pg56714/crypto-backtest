import websocket  # pip install websocket-client
import json


# 當 WebSocket 連接打開時調用的函數
def on_open(ws):
    print("WebSocket 已打開")
    # 訂閱一個頻道
    subscribe = {
        "method": "SUBSCRIBE",
        "params": [
            "btcusdt@kline_1m",  # 訂閱 BTC/USDT 的 1 分鐘 K 線頻道
            "btcusdt@depth",  # 訂閱 BTC/USDT 的訂單簿深度頻道
            "!bookTicker",
        ],
        "id": 1,
    }
    ws.send(json.dumps(subscribe))  # 發送訂閱消息 # 啟動定期發送 pong 幀的線程


# 當從 WebSocket 收到消息時調用的函數
def on_message(ws, message):
    print("收到消息:", message)


# 當發生錯誤時調用的函數
def on_error(ws, error):
    print("發生錯誤:", error)


# 當 WebSocket 連接關閉時調用的函數
def on_close(ws):
    print("WebSocket 已關閉")


# 創建一個 WebSocketApp 實例並設置事件處理程序
ws = websocket.WebSocketApp(
    "wss://fstream.binance.com/ws",
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
    on_close=on_close,
)

# 啟動 WebSocket 連接並永久運行
ws.run_forever()
