import joblib
import numpy as np
import pandas as pd
import json
from config.config import load_config
from live_trading.mt5_trader import get_lot_limits
import shap

# Carrega configuração
cfg = load_config()

# Carregamento dos modelos usando configuração
try:
    market_model = joblib.load(cfg["model_paths"]["market_analysis"])
    risk_action_model = joblib.load(cfg["model_paths"]["risk_action"])
    risk_level_model = joblib.load(cfg["model_paths"]["risk_level"])
    position_size_model = joblib.load(cfg["model_paths"]["position_size"])
    stop_loss_model = joblib.load(cfg["model_paths"]["stop_loss"])
    take_profit_model = joblib.load(cfg["model_paths"]["take_profit"])
    exec_model = joblib.load(cfg["model_paths"]["strategy_exec"])
    label_map = joblib.load(cfg["model_paths"]["exec_labels"])
    print("✅ Modelos carregados com sucesso")
except Exception as e:
    print(f"❌ Erro ao carregar modelos: {e}")
    print("⚠️ Certifique-se de que os modelos foram treinados com dados MT5")
    raise

def _calculate_trend_type(market: dict, threshold=0.001):
    """Calcula o tipo de tendência baseado na diferença entre EMA20 e EMA50"""
    ema_20 = market.get("ema_20", 0)
    ema_50 = market.get("ema_50", 0)
    close = market.get("close", 1)
    
    diff = ema_20 - ema_50
    if abs(diff) < threshold * close:
        return 0  # Neutra
    elif diff > 0:
        return 1  # Alta
    else:
        return -1  # Baixa

def run_autonomous_decision(market: dict, state: dict):
    # Garante que spread_pct está presente
    if "spread_pct" not in market:
        if "spread" in market and "close" in market and market["close"] != 0:
            market["spread_pct"] = market["spread"] / market["close"]
        else:
            market["spread_pct"] = 0.0001  # valor default seguro

    initial_capital = 10000
    capital = np.clip(state.get("capital", initial_capital), 0, 1e7)
    reinvestment_rate = 0.5
    adjusted_capital = initial_capital + (capital - initial_capital) * reinvestment_rate

    atr = market.get("atr", 0)
    if not np.isfinite(atr) or atr > 1e4:
        atr = 0.0

    # Features para modelo de mercado (adaptadas para MT5)
    market_features = {
        "open": market["open"],
        "high": market["high"],
        "low": market["low"],
        "close": market["close"],
        "tick_volume": market.get("tick_volume", market.get("volume", 1000)),
        "ema_20": market["ema_20"],
        "ema_50": market["ema_50"],
        "macd": market["macd"],
        "rsi": market["rsi"],
        "stoch_k": market["stoch_k"],
        "atr": atr,
        "obv": market.get("obv", 0),
        "volume_sma_20": market.get("volume_sma_20", market.get("tick_volume", market.get("volume", 1000))),
        "volatility_stop": market.get("volatility_stop", 0),
        "volatility_score": market.get("volatility_score", atr / market["close"] if market["close"] > 0 else 0),
        "spread_pct": market["spread_pct"]
    }
    

    market_input = pd.DataFrame([market_features])

    signal = int(market_model.predict(market_input)[0])
    confidence = float(market_model.predict_proba(market_input).max(axis=1)[0])

    # --- SHAP: explicabilidade do modelo de mercado ---
    try:
        explainer = shap.Explainer(market_model)
        shap_values = explainer(market_input)
        feature_importances = dict(zip(market_input.columns, shap_values.values[0]))
        sorted_features = sorted(feature_importances.items(), key=lambda x: abs(x[1]), reverse=True)
        print("\n[SHAP] Principais fatores para decisão do modelo de mercado:")
        for feat, val in sorted_features[:5]:
            print(f"  {feat}: {val:.4f}")
    except Exception as e:
        print(f"[SHAP] Falha ao calcular explicações: {e}")
    # --- fim SHAP ---

    # Features para modelo de risco (adaptadas para MT5)
    risk_features = {
        "capital": adjusted_capital,
        "in_position": int(state.get("in_position", False)),
        "drawdown": state.get("drawdown", 0),
        "atr": atr,
        "signal": signal,
        "confidence": confidence,
        "recent_losses": state.get("recent_losses", 0),
        "volatility_score": atr / market["close"] if market["close"] > 0 else 0,
        "rolling_loss_ratio": state.get("rolling_loss_ratio", 0)
    }
    
    # Adiciona features específicas do MT5 se disponíveis
    if "spread_pct" in market:
        risk_features["spread_pct"] = market["spread_pct"]

    risk_input = pd.DataFrame([risk_features])
    risk_input = risk_input.replace([np.inf, -np.inf], np.nan).fillna(0)

    action_code = int(risk_action_model.predict(risk_input)[0])
    risk_level = int(risk_level_model.predict(risk_input)[0])
    raw_position_size = float(position_size_model.predict(risk_input)[0])
    # Ajusta para múltiplo do step e limites do ativo
    min_lot, max_lot, lot_step = get_lot_limits(state.get('symbol', market.get('symbol', 'EURUSD')))
    position_size = max(min_lot, min(max_lot, round(round(raw_position_size / lot_step) * lot_step, 2)))
    if (position_size - min_lot) % lot_step != 0:
        position_size = min_lot + round((position_size - min_lot) / lot_step) * lot_step
    position_size = round(position_size, 2)
    print(f"[Lote] {state.get('symbol', market.get('symbol', 'EURUSD'))}: min={min_lot}, max={max_lot}, step={lot_step}, sugerido={raw_position_size:.4f}, ajustado={position_size:.4f}")
    stop_loss_pct = float(stop_loss_model.predict(risk_input)[0])
    take_profit_pct = float(take_profit_model.predict(risk_input)[0])

    # Features para modelo de execução (adaptadas para MT5)
    exec_features = {
        "signal": signal,
        "confidence": confidence,
        "action_code": action_code,
        "risk_level_code": risk_level,
        "position_size": position_size,
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct,
        "capital": adjusted_capital,
        "in_position": int(state.get("in_position", False)),
        "time_in_trade": state.get("time_in_trade", 0),
        "profit_pct": state.get("profit_pct", 0),
        "trend_type": _calculate_trend_type(market),
        "time_since_last_trade": state.get("time_since_last_trade", 0)
    }
    
    # Adiciona features específicas do MT5 se disponíveis
    if "spread_pct" in market:
        exec_features["spread_pct"] = market["spread_pct"]

    exec_input = pd.DataFrame([exec_features])
    exec_input = exec_input.replace([np.inf, -np.inf], np.nan).fillna(0)

    decision_encoded = int(exec_model.predict(exec_input)[0])
    final_decision = label_map[decision_encoded]

    last_decision = {
        "final_decision": final_decision,
        "signal": signal,
        "confidence": confidence,
        "action_code": action_code,
        "risk_level": risk_level,
        "position_size": position_size,
        "stop_loss_pct": stop_loss_pct,
        "take_profit_pct": take_profit_pct
    }

    try:
        with open("last_decision.json", "w") as f:
            json.dump(last_decision, f)
    except Exception as e:
        print(f"⚠️ Falha ao salvar last_decision.json: {e}")

    return last_decision