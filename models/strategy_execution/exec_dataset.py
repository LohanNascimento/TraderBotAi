import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def generate_exec_dataset_from_market(parquet_path="data/processed/market_features_m15.parquet", symbols=None):
    df = pd.read_parquet(parquet_path).reset_index(drop=True)
    
    # Filtra por símbolos específicos se fornecido
    if symbols is not None:
        df = df[df["symbol"].isin(symbols)].copy()
        print(f"📊 Filtrando por símbolos: {symbols}")
    
    print(f"📈 Dataset carregado: {len(df)} registros")

    # --- Tipo de tendência ---
    def get_trend_type(row, threshold=0.001):
        diff = row["ema_20"] - row["ema_50"]
        if abs(diff) < threshold * row["close"]:
            return 0  # Neutra
        elif diff > 0:
            return 1  # Alta
        else:
            return -1  # Baixa
    df["trend_type"] = df.apply(get_trend_type, axis=1)

    # --- Simulação de sinais e confiança (mantém como estava) ---
    df["signal"] = np.random.choice([-1, 0, 1], len(df))  # ou use modelo 1
    df["confidence"] = np.clip(np.random.normal(0.7, 0.15, len(df)), 0, 1)

    df["action_code"] = df["signal"].apply(lambda x: 0 if x == 1 else (1 if x == 0 else 2))
    df["risk_level_code"] = df["atr"].apply(lambda x: 0 if x < 0.01 else (1 if x < 0.02 else 2))
    df["position_size"] = df["risk_level_code"].apply(lambda x: 0.12 - 0.04 * x)
    df["stop_loss_pct"] = df["risk_level_code"].apply(lambda x: 0.01 + 0.005 * x)
    df["take_profit_pct"] = df["risk_level_code"].apply(lambda x: 0.03 + 0.01 * x)

    # Adiciona ruído e complexidade para evitar vazamento de dados
    df["position_size"] *= np.random.normal(1, 0.1, len(df))
    df["stop_loss_pct"] *= np.random.normal(1, 0.1, len(df))
    df["take_profit_pct"] *= np.random.normal(1, 0.1, len(df))
    df["profit_pct"] = np.random.normal(0.01, 0.03, len(df))
    df["time_in_trade"] = np.random.randint(0, 120, len(df))
    df["in_position"] = np.random.choice([0, 1], len(df))
    df["capital"] = 10000  # USD para MT5

    # --- time_since_last_trade ---
    time_since_last_trade = []
    last_trade_idx = -1
    for idx, row in df.iterrows():
        if idx == 0 or (idx > 0 and row["in_position"] == 1 and df.loc[idx-1, "in_position"] == 0):
            last_trade_idx = idx
        time_since_last_trade.append(idx - last_trade_idx)
    df["time_since_last_trade"] = time_since_last_trade

    def decide(row):
        # A lógica de decisão é mais complexa e menos determinística
        if row["in_position"] == 0:
            if row["signal"] == 1 and row["confidence"] > 0.6 and row["risk_level_code"] < 5:
                return "buy"
            else:
                return "no_action"
        else:
            if row["signal"] == -1 and row["confidence"] > 0.6:
                return "sell"
            if row["profit_pct"] > row["take_profit_pct"]:
                return "sell"  # Realiza lucro
            if row["profit_pct"] < -row["stop_loss_pct"]:
                return "sell"  # Stop loss
            if row["time_in_trade"] > 100 and row["profit_pct"] < 0.005:
                return "partial_exit"
            if row["confidence"] > 0.8 and row["risk_level_code"] == 0:
                return "move_stop"
            else:
                return "hold"

    df["execution_decision"] = df.apply(decide, axis=1)
    df = df.dropna()  # Garante que não há NaNs
    df["decision_encoded"] = df["execution_decision"].astype("category").cat.codes
    
    label_map = dict(enumerate(df["execution_decision"].astype("category").cat.categories))

    # Features adaptadas para MT5
    features = [
        "signal", "confidence", "action_code", "risk_level_code",
        "position_size", "stop_loss_pct", "take_profit_pct",
        "capital", "in_position", "time_in_trade", "profit_pct",
        "trend_type", "time_since_last_trade", "spread_pct"
    ]
    

    X = df[features]
    y = df["decision_encoded"]
    
    # Validação para garantir que X e y têm o mesmo tamanho
    if len(X) != len(y):
        raise ValueError("X e y têm tamanhos diferentes após o pré-processamento.")

    print(f"📊 Features utilizadas: {features}")
    print(f"📈 Tamanho do dataset: {len(X)} registros")
    print(f"🎯 Classes de decisão: {label_map}")

    return {
        "X": X,
        "y": y,
        "label_map": label_map
    }
