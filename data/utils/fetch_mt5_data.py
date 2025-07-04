import os
import time
import sys

# Adiciona o diretório raiz ao path para encontrar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from live_trading.mt5_api import connect, shutdown, fetch_rates
from config.config import load_config

def main():
    # Carrega configuração
    cfg = load_config()
    symbols = cfg["general"]["symbols"]
    timeframe_str = cfg["general"]["timeframe"]
    
    # Mapeia timeframe string para constante MT5
    timeframe_map = {
        "M1": 1, "M5": 5, "M15": 15, "M30": 30,
        "H1": 16385, "H4": 16388, "D1": 16408
    }
    
    timeframe = timeframe_map.get(timeframe_str, 15)  # Default M15
    N_CANDLES = 5000
    OUTPUT_DIR = "data/raw"
    
    print(f"🔄 Iniciando coleta de dados MT5...")
    print(f"📊 Símbolos: {symbols}")
    print(f"⏰ Timeframe: {timeframe_str}")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    connect()

    for symbol in symbols:
        try:
            print(f"📈 Coletando {symbol}...")
            df = fetch_rates(symbol, timeframe=timeframe, n=N_CANDLES)
            path = os.path.join(OUTPUT_DIR, f"{symbol}_{timeframe_str}.csv")
            df.to_csv(path)
            print(f"✅ Dados salvos para {symbol}: {path}")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Erro ao obter {symbol}: {e}")

    shutdown()
    print("🎉 Coleta de dados concluída!")

if __name__ == "__main__":
    main()
