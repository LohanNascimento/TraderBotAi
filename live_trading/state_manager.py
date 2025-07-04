import json
import os

def save_position_state(state: dict, path="position_state.json"):
    with open(path, "w") as f:
        json.dump(state, f)

def load_position_state(path="position_state.json") -> dict:
    if not os.path.exists(path):
        return {
            "in_position": False,
            "entry_price": 0.0,
            "time_in_trade": 0,
            "profit_pct": 0.0
        }
    with open(path, "r") as f:
        return json.load(f)
