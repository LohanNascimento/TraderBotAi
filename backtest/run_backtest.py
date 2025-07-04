import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
from core.logic import run_autonomous_decision
from backtest.trader_simulator import TraderSimulator
from tqdm import tqdm
from config.config import load_config
from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np
cfg = load_config()

def run_backtest(start_index=50):
    symbol = cfg["general"].get("symbols", ["EURUSD"])[0]
    lot_size = cfg.get("mt5", {}).get("lot_size", 0.01)
    sim = TraderSimulator(initial_capital=cfg["trading"]["initial_capital"], symbol=symbol, lot_size=lot_size)
    data = pd.read_parquet(cfg["general"]["data_path"])
    #print(data.head())
    print("🚀 Iniciando backtest...")
    
    # Variáveis para tracking de performance
    recent_trades = []  # Lista para calcular rolling_loss_ratio
    max_capital = sim.capital
    last_trade_time = start_index  # Para calcular time_since_last_trade
    decision_counter = defaultdict(int)
    
    # Envolve o loop com tqdm
    for i in tqdm(range(start_index, len(data) - 1), desc="🔄 Processando"):
        row = data.iloc[i]
        next_row = data.iloc[i + 1]

        market = row.to_dict()

        # Calcula drawdown
        current_drawdown = (max_capital - sim.capital) / max_capital if max_capital > 0 else 0
        max_capital = max(max_capital, sim.capital)
        
        # Calcula rolling_loss_ratio (últimos 10 trades)
        if len(recent_trades) >= 10:
            recent_trades.pop(0)  # Remove o trade mais antigo
        
        # Adiciona resultado do último trade se existir
        if sim.trade_log and len(sim.trade_log) > 0:
            last_trade = sim.trade_log[-1]
            if last_trade["pnl"] < 0:
                recent_trades.append(0)  # Loss
            else:
                recent_trades.append(1)  # Win
        
        rolling_loss_ratio = (len([t for t in recent_trades if t == 0]) / len(recent_trades)) if recent_trades else 0
        
        # Calcula recent_losses (últimos 3 trades)
        recent_losses = 0
        if len(sim.trade_log) >= 3:
            for trade in sim.trade_log[-3:]:
                if trade["pnl"] < 0:
                    recent_losses += 1

        state = {
            "capital": sim.capital,
            "in_position": int(sim.position is not None),
            "drawdown": current_drawdown,
            "time_in_trade": (i - sim.position["entry_time"]) if sim.position else 0,
            "recent_losses": recent_losses,
            "profit_pct": 0.0,
            "rolling_loss_ratio": rolling_loss_ratio,
            "time_since_last_trade": i - last_trade_time
        }

        sim.check_stop_or_tp(row["close"], i)

        # Roda a decisão uma vez por passo
        decision = run_autonomous_decision(market, state)
        if decision["final_decision"] == "buy":
            print(f"🟢 BUY SIGNAL at index {i} | price: {row['close']} | confidence: {decision['confidence']:.2f}")
        elif decision["final_decision"] == "sell":
            print(f"🔴 SELL SIGNAL at index {i} | price: {row['close']} | confidence: {decision['confidence']:.2f}")
        decision_counter[decision["final_decision"]] += 1
        # Executa a ação com base na decisão e no estado atual
        if sim.position:
            if (decision["final_decision"] == "sell" and sim.position["order_type"] == "buy") or \
               (decision["final_decision"] == "buy" and sim.position["order_type"] == "sell"):
                sim.exit_position(row["close"], i, "model_exit")
                last_trade_time = i  # Atualiza o tempo do último trade
            elif decision["final_decision"] == "move_stop":
                # Ajusta o stop_price com base no tipo de ordem
                if sim.position["order_type"] == "buy":
                    sim.position["stop_price"] = row["close"] * (1 - decision["stop_loss_pct"])
                elif sim.position["order_type"] == "sell":
                    sim.position["stop_price"] = row["close"] * (1 + decision["stop_loss_pct"])
        else:  # Se não está em posição
            if decision["final_decision"] == "buy":
                sim.enter_position(row["close"], decision["position_size"],
                                   decision["stop_loss_pct"], decision["take_profit_pct"], i, order_type="buy")
                last_trade_time = i  # Atualiza o tempo do último trade
            elif decision["final_decision"] == "sell":
                sim.enter_position(row["close"], decision["position_size"],
                                   decision["stop_loss_pct"], decision["take_profit_pct"], i, order_type="sell")
                last_trade_time = i  # Atualiza o tempo do último trade

        sim.log_equity()

    # Resultados finais
    df_equity = pd.DataFrame(sim.equity_curve, columns=["equity"])
    df_trades = pd.DataFrame(sim.trade_log)
    df_equity.to_csv("backtest/equity_curve.csv", index=False)
    df_trades.to_csv("backtest/trade_log.csv", index=False)

    # --- NOVAS MÉTRICAS ---
    metrics = calculate_metrics(sim.equity_curve, sim.trade_log)
    print("\n📊 Métricas do Backtest:")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2%}")
    print(f"Sharpe Ratio: {metrics['sharpe']:.2f}")
    print(f"Acurácia (Win Rate): {metrics['win_rate']:.2%}")
    print(f"Média Lucro: {metrics['avg_win']:.2f}")
    print(f"Média Prejuízo: {metrics['avg_loss']:.2f}")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Recovery Factor: {metrics['recovery_factor']:.2f}")
    plot_equity_curve(sim.equity_curve)
    print("Gráfico da curva de capital salvo em backtest/equity_curve.png")

    print("✅ Backtest completo.")
    print(f"💰 Capital final: {sim.capital:.2f}")
    print(f"📈 Nº de trades: {len(sim.trade_log)}")
    print("📊 Distribuição de decisões do modelo:")
    for k, v in decision_counter.items():
        print(f"  {k}: {v}")

def calculate_metrics(equity_curve, trade_log):
    equity = np.array(equity_curve)
    returns = np.diff(equity) / equity[:-1]
    # Drawdown
    running_max = np.maximum.accumulate(equity)
    drawdown = (equity - running_max) / running_max
    max_drawdown = drawdown.min()
    # Sharpe Ratio (risk-free = 0)
    sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
    # Trade stats
    trades = trade_log
    if len(trades) > 0:
        pnl = np.array([t["pnl"] for t in trades])
        wins = pnl > 0
        losses = pnl < 0
        win_rate = wins.sum() / len(pnl)
        avg_win = pnl[wins].mean() if wins.any() else 0
        avg_loss = pnl[losses].mean() if losses.any() else 0
        profit_factor = pnl[wins].sum() / (abs(pnl[losses].sum()) + 1e-8) if losses.any() else np.inf
        recovery_factor = (equity[-1] - equity[0]) / abs(max_drawdown * equity[0]) if max_drawdown != 0 else np.inf
    else:
        win_rate = avg_win = avg_loss = profit_factor = recovery_factor = 0
    return {
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "profit_factor": profit_factor,
        "recovery_factor": recovery_factor
    }

def plot_equity_curve(equity_curve, filename="backtest/equity_curve.png"):
    plt.figure(figsize=(12, 6))
    plt.plot(equity_curve, label="Equity Curve", color='blue')

    # Calcular e plotar Drawdown
    equity_array = np.array(equity_curve)
    peak = np.maximum.accumulate(equity_array)
    drawdown = (peak - equity_array) / peak

    plt.fill_between(range(len(equity_array)), equity_array, peak, where=equity_array < peak, color='red', alpha=0.3, label='Drawdown')

    plt.title("Curva de Capital com Drawdown")
    plt.xlabel("Período")
    plt.ylabel("Capital")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename)
    plt.close()

if __name__ == "__main__":
    run_backtest()
