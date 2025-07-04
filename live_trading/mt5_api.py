import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
from config.config import load_config
import MetaTrader5 as mt5

_cfg = None
_connected = False

def get_config():
    global _cfg
    if _cfg is None:
        _cfg = load_config()
    return _cfg

def connect():
    global _connected
    
    if _connected:
        return True
        
    cfg = get_config()
    mt5_config = cfg["mt5"]
    
    # Inicializa MT5
    if not mt5.initialize():
        print(f"❌ Erro ao inicializar MT5: {mt5.last_error()}")
        return False
    
    # Login na conta
    if not mt5.login(
        login=int(mt5_config["account"]),
        password=mt5_config["password"],
        server=mt5_config["server"]
    ):
        print(f"❌ Erro no login MT5: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    print("✅ Conectado ao MetaTrader 5")
    _connected = True
    return True

def disconnect():
    global _connected
    if _connected:
        mt5.shutdown()
        _connected = False
        print("🔌 Desconectado do MetaTrader 5")

def get_latest_candle(symbol: str, interval="M15") -> dict:
    """Obtém o último candle de um símbolo"""
    if not connect():
        return None
    
    # Mapeia timeframe string para constante MT5
    timeframe_map = {
        "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, 
        "M15": mt5.TIMEFRAME_M15, "M30": mt5.TIMEFRAME_M30,
        "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4, 
        "D1": mt5.TIMEFRAME_D1
    }
    
    timeframe = timeframe_map.get(interval, mt5.TIMEFRAME_M15)
    
    # Obtém o último candle
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, 1)
    if rates is None or len(rates) == 0:
        print(f"❌ Erro ao obter dados para {symbol}")
        return None
    
    candle = rates[0]
    return {
        "open": float(candle["open"]),
        "high": float(candle["high"]),
        "low": float(candle["low"]),
        "close": float(candle["close"]),
        "volume": float(candle["tick_volume"]),
        "timestamp": int(candle["time"]),
        "spread": float(candle["spread"])
    }

def fetch_rates(symbol: str, timeframe=mt5.TIMEFRAME_M15, n=5000):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n)
    if rates is None or len(rates) == 0:
        raise ValueError(f"Nenhum dado retornado para {symbol}")
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s")
    return df.set_index("time")