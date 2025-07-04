import time
from config.config import load_config
from live_trading.mt5_api import get_latest_candle
from live_trading.mt5_trader import place_market_order, get_balance
from core.signals import add_indicators
from core.logic import run_autonomous_decision
from live_trading.risk_guard import RiskGuard
from live_trading.state_manager import save_position_state, load_position_state
import pandas as pd
from live_trading.telegram_control import start_telegram_thread, is_paused, is_running

state = load_position_state()
cfg = load_config()

try:
    risk_guard = RiskGuard.load("risk_state.json")
    print("🔄 Estado de risco carregado com sucesso.")
except FileNotFoundError:
    print("📦 Nenhum estado salvo. Iniciando novo controle de risco.")
    risk_guard = RiskGuard(
        initial_capital=cfg["trading"]["initial_capital"],
        max_drawdown=cfg["trading"]["max_drawdown"],
        max_consecutive_losses=3,
        cooldown_steps=3
    )

# Suporte a múltiplos ativos
symbols = cfg["general"].get("symbols")
if symbols is None:
    symbol = cfg["general"].get("symbol")
    if symbol is None:
        raise ValueError("Nenhum símbolo definido em cfg['general']['symbols'] ou cfg['general']['symbol']")
    symbols = [symbol]
# Garante que symbols seja uma lista plana de strings
if isinstance(symbols, str):
    symbols = [symbols]
elif isinstance(symbols, list) and len(symbols) == 1 and isinstance(symbols[0], list):
    symbols = symbols[0]

interval = cfg["general"]["timeframe"]
capital = cfg["trading"]["initial_capital"]
min_conf = cfg["trading"]["min_confidence"]

price_buffers = {symbol: [] for symbol in symbols}  # Histórico para cada ativo
MAX_BUFFER = 5

# Estado por ativo
state = {symbol: {
    "capital": capital,
    "in_position": False,
    "entry_price": 0.0,
    "drawdown": 0,
    "recent_losses": 0,
    "time_in_trade": 0,
    "profit_pct": 0
} for symbol in symbols}

def run_trader_bot():
    print("🤖 Robô iniciado em tempo real (MT5 PAPER TRADING)...")
    global state

    start_telegram_thread()  # Inicia o controle do Telegram

    while True:
        # Checa se o bot deve ser parado
        if not is_running():
            print("🛑 Bot encerrado por comando do Telegram.")
            break

        # Checa se o bot está pausado
        if is_paused():
            print("⏸️ Bot pausado por comando do Telegram. Aguardando retomar...")
            time.sleep(10)
            continue

        for symbol in symbols:
            candle = get_latest_candle(symbol, interval)
            price_buffers[symbol].append(candle)

            # BLOQUEIOS DE RISCO
            blocked_reason = risk_guard.is_blocked()
            if blocked_reason:
                print(f"🚫 ROBÔ BLOQUEADO: {blocked_reason}")
                return

            if risk_guard.check_cooldown():
                print("🕒 Cooldown ativo. Aguardando...")
                time.sleep(60)
                continue

            if len(price_buffers[symbol]) < MAX_BUFFER:
                print(f"⌛ [{symbol}] Aguardando dados suficientes...")
                time.sleep(1)
                continue

            buffer_slice = price_buffers[symbol][-MAX_BUFFER:]
            filtered_buffer = [x for x in buffer_slice if x is not None]
            df = pd.DataFrame(filtered_buffer)
            df = add_indicators(df)
            latest = df.iloc[-1].to_dict()

            decision = run_autonomous_decision(latest, state[symbol])

            if not state[symbol]["in_position"] and decision["final_decision"] == "buy":
                usd_balance = get_balance("USD")
                if decision["confidence"] >= min_conf and usd_balance > 10:
                    qty = decision["position_size"]  # agora já é lotes
                    order = place_market_order(symbol, "BUY", round(qty, 2))
                    if order:
                        state[symbol]["in_position"] = True
                        state[symbol]["entry_price"] = latest["close"]
                        state[symbol]["time_in_trade"] = 0
                        state[symbol]["profit_pct"] = 0.0
                        save_position_state(state)
                        print(f"🟢 [{symbol}] COMPRA executada: {qty:.4f} @ {latest['close']:.5f}")

            elif state[symbol]["in_position"] and decision["final_decision"] in ["sell", "partial_exit"]:
                balance = get_balance(symbol)
                if balance > 0.0001:
                    order = place_market_order(symbol, "SELL", round(balance, 6))
                    if order:
                        state[symbol]["in_position"] = False
                        state[symbol]["entry_price"] = 0.0
                        state[symbol]["time_in_trade"] = 0
                        state[symbol]["profit_pct"] = 0.0
                        save_position_state(state)
                        print(f"🔴 [{symbol}] VENDA executada @ {latest['close']:.5f}")

                        profit_pct = (latest["close"] - state[symbol]["entry_price"]) / state[symbol]["entry_price"]
                        risk_guard.update_after_trade(profit_pct)
                        risk_guard.save("risk_state.json")

                        if profit_pct < 0:
                            print(f"📉 [{symbol}] PERDA: {profit_pct*100:.2f}% | DD: {risk_guard.drawdown*100:.2f}%")
                        else:
                            print(f"📈 [{symbol}] LUCRO: {profit_pct*100:.2f}%")

            # Atualização do tempo em posição
            if state[symbol]["in_position"]:
                state[symbol]["time_in_trade"] += 1
                entry = state[symbol]["entry_price"]
                state[symbol]["profit_pct"] = (latest["close"] - entry) / entry
                save_position_state(state)

        time.sleep(60)  # aguarda o próximo candle
