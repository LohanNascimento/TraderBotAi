import time
import os
import json
from live_trading.mt5_api import get_latest_candle

STATE_FILE = "paper_state.json"
TRADE_LOG = "paper_trade_log.csv"

# Estado inicial padrão (USD para MT5)
initial_state = {
    "USD": 10000.0,
    "positions": {}
}


def load_paper_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return initial_state.copy()


def save_paper_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)


state = load_paper_state()




def place_market_order(symbol: str, side: str, quantity: float):
    """Simula ordem de mercado para MT5"""
    global state
    price = get_latest_candle(symbol)["close"]
    positions = state["positions"]
    pos = positions.get(symbol, {"quantity": 0.0, "entry_price": 0.0, "in_position": False})
    
    if side == "BUY" and not pos["in_position"]:
        cost = quantity * price
        if state["USD"] >= cost:
            pos["quantity"] = quantity
            pos["entry_price"] = price
            pos["in_position"] = True
            state["USD"] -= cost
            positions[symbol] = pos
            log_trade(symbol, "BUY", quantity, price)
            save_paper_state(state)
            return {"status": "FILLED"}
        else:
            print("Saldo insuficiente para compra.")
            return None
    elif side == "SELL" and pos["in_position"]:
        proceeds = pos["quantity"] * price
        state["USD"] += proceeds
        log_trade(symbol, "SELL", pos["quantity"], price)
        pos["quantity"] = 0.0
        pos["entry_price"] = 0.0
        pos["in_position"] = False
        positions[symbol] = pos
        save_paper_state(state)
        return {"status": "FILLED"}
    return None


def get_balance(asset="USD"):
    """Retorna saldo em USD (moeda base para MT5)"""
    global state
    if asset == "USD":
        return state["USD"]
    # Para ativos, retorna quantidade em posição aberta
    pos = state["positions"].get(asset, {"quantity": 0.0})
    return pos["quantity"]


def log_trade(symbol, side, qty, price):
    exists = os.path.exists(TRADE_LOG)
    with open(TRADE_LOG, "a") as f:
        if not exists:
            f.write("timestamp,symbol,side,qty,price\n")
        f.write(f"{int(time.time())},{symbol},{side},{qty},{price}\n")