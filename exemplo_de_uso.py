from core.logic import run_autonomous_decision

market = {
    "open": 26000, "high": 26100, "low": 25900, "close": 26050, "volume": 1200,
    "ema_20": 25980, "ema_50": 25800, "macd": 0.002, "rsi": 65,
    "stoch_k": 80, "atr": 0.015
}

state = {
    "capital": 10000,
    "in_position": 0,
    "drawdown": 0.02,
    "time_in_trade": 0,
    "recent_losses": 1,
    "profit_pct": 0.0
}

decision = run_autonomous_decision(market, state)
print(decision)
