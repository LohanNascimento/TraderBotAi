from binance.client import Client
import os
from config.config import load_config
import time
from binance.client import Client

_cfg = None
_client = None

def get_client():
    global _cfg, _client
    if _client is not None:
        return _client

    _cfg = load_config()
    api_key = _cfg["binance"]["api_key"]
    api_secret = _cfg["binance"]["api_secret"]

    client = Client(api_key, api_secret)

    # Ativa Testnet, se for o caso
    if _cfg["binance"].get("testnet", True):
        client.API_URL = 'https://testnet.binancefuture.com/api'

    # Sincroniza o offset do timestamp
    try:
        server_time = client.get_server_time()
        local_time = int(time.time() * 1000)
        client.timestamp_offset = server_time['serverTime'] - local_time
    except Exception as e:
        print(f"⚠️ Erro ao sincronizar horário com Binance: {e}")
        client.timestamp_offset = 0

    _client = client
    return _client

def get_latest_candle(symbol: str, interval="15m") -> dict:
    client = get_client()
    candles = client.get_klines(symbol=symbol, interval=interval, limit=1)
    c = candles[0]
    return {
        "open": float(c[1]),
        "high": float(c[2]),
        "low": float(c[3]),
        "close": float(c[4]),
        "volume": float(c[5]),
        "timestamp": int(c[0])
    }

def place_market_order(symbol: str, side: str, quantity: float):
    """side: 'BUY' or 'SELL'"""
    client = get_client()
    try:
        order = client.create_order(
            symbol=symbol,
            side=side,
            type=Client.ORDER_TYPE_MARKET,
            quantity=quantity
        )
        return order
    except Exception as e:
        print(f"❌ Erro ao enviar ordem: {e}")
        return None

def get_balance(asset="USDT"):
    client = get_client()
    info = client.get_asset_balance(asset=asset)
    return float(info["free"]) if info else 0

if __name__ == "__main__":
    client = get_client()
    print("✅ Client criado e sincronizado!")

    # Testa pegar saldo
    try:
        usdt_balance = get_balance("USDT")
        print(f"Saldo USDT: {usdt_balance}")
    except Exception as e:
        print(f"Erro ao obter saldo: {e}")

    # Testa pegar candle
    try:
        candle = get_latest_candle("BTCUSDT", "15m")
        print(f"Último candle BTCUSDT 15m: {candle}")
    except Exception as e:
        print(f"Erro ao obter candle: {e}")

