from config.config import load_config

cfg = load_config()
mode = cfg["general"]["mode"]

if mode == "backtest":
    from backtest.run_backtest import run_backtest
    run_backtest()
elif mode == "live":
    from live_trading.trader_bot import run_trader_bot
    run_trader_bot()
else:
    print(f"❌ Modo desconhecido: {mode}")
