from flask import Flask, render_template, jsonify
import json
from live_trading.mt5_trader import get_lot_limits

app = Flask(__name__)

def load_json(path, default={}):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/data")
def data():
    positions = load_json("position_state.json")
    risk = load_json("risk_state.json")
    decision = load_json("last_decision.json")
    # Lista de trades em andamento
    open_trades = []
    lot_limits = {}
    for symbol, pos in positions.items():
        if pos.get("in_position"):
            open_trades.append({"symbol": symbol, **pos})
        min_lot, max_lot, lot_step = get_lot_limits(symbol)
        lot_limits[symbol] = {"min": min_lot, "max": max_lot, "step": lot_step}
    return jsonify({
        "positions": positions,
        "open_trades": open_trades,
        "risk": risk,
        "decision": decision,
        "lot_limits": lot_limits
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
