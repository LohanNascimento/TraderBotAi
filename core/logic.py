import joblib
import numpy as np
import pandas as pd
import json
from config.config import load_config
from live_trading.mt5_trader import get_lot_limits
# Removido shap por enquanto, pois é específico para modelos scikit-learn.
# Para LSTMs, alternativas como LIME ou Captum (PyTorch) ou tf-explain (TF) seriam necessárias.
# import shap

# Importa o nosso novo wrapper LSTM
from models.market_analysis.lstm_model_wrapper import LSTMModelWrapper

# Carrega configuração
cfg = load_config()

# Carregamento dos modelos usando configuração
try:
    # Carregar o LSTM Wrapper
    lstm_model_path = cfg["model_paths"]["lstm_market_model"]
    lstm_scaler_path = cfg["model_paths"]["lstm_market_scaler"]

    # Parâmetros do wrapper podem vir da config ou usar defaults
    lstm_params = cfg.get("lstm_wrapper_params", {})
    timesteps = lstm_params.get("timesteps", 20) # Default no wrapper é 20
    expected_features_lstm = lstm_params.get("expected_features", None) # Default no wrapper é uma lista específica

    # Instanciar o wrapper LSTM como o novo 'market_model'
    market_model = LSTMModelWrapper(
        model_path=lstm_model_path,
        scaler_path=lstm_scaler_path,
        timesteps=timesteps,
        expected_features=expected_features_lstm
    )
    print(f"✅ Modelo de Análise de Mercado (LSTM Wrapper) carregado.")

    risk_action_model = joblib.load(cfg["model_paths"]["risk_action"])
    risk_level_model = joblib.load(cfg["model_paths"]["risk_level"])
    position_size_model = joblib.load(cfg["model_paths"]["position_size"])
    stop_loss_model = joblib.load(cfg["model_paths"]["stop_loss"])
    take_profit_model = joblib.load(cfg["model_paths"]["take_profit"])
    exec_model = joblib.load(cfg["model_paths"]["strategy_exec"])
    label_map = joblib.load(cfg["model_paths"]["exec_labels"])
    print("✅ Modelos de Risco e Execução carregados com sucesso.")
except Exception as e:
    print(f"❌ Erro ao carregar modelos: {e}")
    print("⚠️ Verifique os caminhos dos modelos e a configuração.")
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
        atr = 0.0 # Evita ATRs inválidos que podem quebrar a normalização ou o modelo

    # O dicionário 'market' já contém as features que o LSTMModelWrapper espera.
    # O wrapper é responsável por selecionar as 'expected_features' e formatá-las.
    # Precisamos passar o símbolo do ativo para o wrapper.
    current_symbol = state.get('symbol', market.get('symbol', 'DEFAULT_LSTM_SYMBOL'))
    # DEFAULT_LSTM_SYMBOL é um fallback se nenhum símbolo for encontrado,
    # mas o ideal é que 'symbol' sempre esteja presente no estado ou nos dados de mercado.

    # O LSTMModelWrapper.predict() espera um dicionário de dados de mercado e o símbolo.
    # As features são selecionadas e pré-processadas dentro do wrapper.
    signal, confidence = market_model.predict(market, symbol=current_symbol)
    signal = int(signal)
    confidence = float(confidence)
    
    # --- SHAP: Explicabilidade ---
    # A explicabilidade com SHAP para modelos scikit-learn (como o RandomForest anterior)
    # não se aplica diretamente a modelos Keras/TensorFlow como o LSTM.
    # Seriam necessárias outras bibliotecas/técnicas (ex: LIME, Captum, tf-explain, Integrated Gradients).
    # Por enquanto, vamos remover a seção SHAP ou comentá-la.
    # print("[INFO] Explicabilidade SHAP não implementada para o modelo LSTM nesta versão.")
    # --- fim SHAP ---


    # Features para modelo de risco (adaptadas para MT5)
    # Estas features permanecem as mesmas, pois os modelos de risco não mudaram.
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