import pandas as pd
from config.config import load_config

def get_pip_value(symbol, lot_size):
    # Para pares padrão (ex: EURUSD), 1 pip = 0.0001, 1 lote = 100.000 unidades, pip value = $10 por lote
    # Para JPY (ex: USDJPY), 1 pip = 0.01, pip value = $10 por lote
    if symbol.endswith('JPY'):
        pip_size = 0.01
    else:
        pip_size = 0.0001
    # pip_value = (pip_size / preço) * lot_size * 100000 (para USD como moeda de cotação)
    # Para backtest, simplificamos: pip_value = $10 por lote padrão
    pip_value_per_lot = 10
    return pip_size, pip_value_per_lot * lot_size

class TraderSimulator:
    def __init__(self, initial_capital=10000, symbol="EURUSD", lot_size=None):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.balance = initial_capital
        self.position = None
        self.equity_curve = []
        self.trade_log = []
        self.symbol = symbol
        cfg = load_config()
        self.lot_size = lot_size if lot_size is not None else cfg.get("mt5", {}).get("lot_size", 0.01)
        self.pip_size, self.pip_value = get_pip_value(self.symbol, self.lot_size)

    def enter_position(self, price, lotes, stop_loss_pct, take_profit_pct, time_step, order_type="buy"):
        # lotes: quantidade de lotes a ser operada (ex: 0.01 a 0.1)
        self.position = {
            "entry_price": price,
            "lotes": lotes,
            "order_type": order_type,
            "stop_price": price - stop_loss_pct * price if order_type == "buy" else price + stop_loss_pct * price,
            "take_profit_price": price + take_profit_pct * price if order_type == "buy" else price - take_profit_pct * price,
            "entry_time": time_step,
            "stop_loss_pct": stop_loss_pct,
            "take_profit_pct": take_profit_pct
        }

    def exit_position(self, price, time_step, reason=None):
        entry = self.position
        lotes = entry["lotes"]
        # Calcula o PnL em pips
        if entry["order_type"] == "buy": # Ordem de compra (long)
            pnl_pips = (price - entry["entry_price"]) / self.pip_size
        elif entry["order_type"] == "sell": # Ordem de venda (short)
            pnl_pips = (entry["entry_price"] - price) / self.pip_size
        else:
            pnl_pips = 0 # Caso inesperado

        # PnL em USD
        pnl = pnl_pips * self.pip_value * lotes
        self.balance += pnl
        self.capital += pnl
        self.capital = min(self.capital, 1e7)

        self.trade_log.append({
            "entry_price": round(entry["entry_price"], 5),
            "exit_price": round(price, 5),
            "lotes": round(lotes, 2),
            "entry_time": entry["entry_time"],
            "exit_time": time_step,
            "pnl": round(pnl, 5),
            "pnl_pips": round(pnl_pips, 5),
            "reason": reason
        })

        self.position = None

    def log_equity(self):
        equity = min(self.capital, 1e7)
        self.equity_curve.append(equity)

    def save_results(self):
        pd.DataFrame(self.equity_curve, columns=["equity"]).to_csv("equity_curve.csv", index=False)
        pd.DataFrame(self.trade_log).to_csv("trade_log.csv", index=False)

    def check_stop_or_tp(self, price, time_step):
        if self.position:
            if self.position["order_type"] == "buy":
                if price <= self.position["stop_price"]:
                    self.exit_position(self.position["stop_price"], time_step, reason="stop_loss")
                elif price >= self.position["take_profit_price"]:
                    self.exit_position(self.position["take_profit_price"], time_step, reason="take_profit")
            elif self.position["order_type"] == "sell":
                if price >= self.position["stop_price"]:
                    self.exit_position(self.position["stop_price"], time_step, reason="stop_loss")
                elif price <= self.position["take_profit_price"]:
                    self.exit_position(self.position["take_profit_price"], time_step, reason="take_profit")