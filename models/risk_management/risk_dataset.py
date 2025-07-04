import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

def generate_risk_dataset_from_market_data(parquet_path="data/processed/market_features_m15.parquet", symbols=None):
    df = pd.read_parquet(parquet_path).reset_index(drop=True)
    
    # Filtra por símbolos específicos se fornecido
    if symbols is not None:
        df = df[df["symbol"].isin(symbols)].copy()
        print(f"📊 Filtrando por símbolos: {symbols}")
    
    print(f"📈 Dataset carregado: {len(df)} registros")

    df["signal"] = np.random.choice([-1, 0, 1], size=len(df))
    df["confidence"] = np.clip(np.random.normal(0.7, 0.15, size=len(df)), 0, 1)
    df["capital"] = 10_000  # USD para MT5
    df["in_position"] = np.random.choice([0, 1], size=len(df), p=[0.6, 0.4])
    df["drawdown"] = np.clip(np.random.normal(0.02, 0.015, len(df)), 0, 0.15)
    df["recent_losses"] = np.random.randint(0, 4, len(df))

    # rolling_loss_ratio
    np.random.seed(42)
    trade_results = np.random.choice([0, 1], size=len(df), p=[0.4, 0.6])
    window = 10
    rolling_loss_ratio = pd.Series(trade_results).rolling(window).apply(lambda x: (x == 0).sum() / window, raw=True).fillna(0)
    df["rolling_loss_ratio"] = rolling_loss_ratio.values

    # volatilidade e tamanho de posição (agora em lotes, não percentual)
    # position_size agora representa lotes (ex: 0.01 a 0.1)
    base_lot = 0.05
    k_vol = 0.3
    k_loss = 0.1
    df["volatility_score"] = df["atr"] / df["close"]
    # Gera valores de lotes entre 0.01 e 0.1, ajustando por volatilidade e perdas recentes
    df["position_size"] = base_lot / (1 + k_vol * df["volatility_score"] + k_loss * df["rolling_loss_ratio"])
    df["position_size"] = df["position_size"].clip(0.01, 0.1)
    df["position_size"] += np.random.normal(0, 0.002, len(df))  # ruído leve
    df["position_size"] = df["position_size"].clip(0.01, 0.1)

    # Códigos de ação
    def simulate_action(row):
        if row["drawdown"] > 0.1:
            return 2  # avoid
        elif row["in_position"] and row["recent_losses"] >= 2:
            return 1  # reduce
        else:
            return 0  # enter

    df["action_code"] = df.apply(simulate_action, axis=1)

    # Nível de risco com reforço na classe 2
    df["risk_level_code"] = df["drawdown"].apply(lambda x: 2 if x > 0.08 else (1 if x > 0.03 else 0))

    # Aumentar classe 2 artificialmente para treinar melhor
    high_risk_samples = df[df["risk_level_code"] == 2]
    if len(high_risk_samples) > 0:
        extra_high_risk = high_risk_samples.sample(n=min(100, len(high_risk_samples)), replace=True)
        df = pd.concat([df, extra_high_risk], ignore_index=True)
    else:
        print("Aviso: Não foram encontradas amostras de alto risco. Criando amostras sintéticas...")
        synthetic_samples = df.sample(n=min(50, len(df)), replace=True).copy()
        synthetic_samples["drawdown"] = np.random.uniform(0.09, 0.15, len(synthetic_samples))
        synthetic_samples["risk_level_code"] = 2
        synthetic_samples["action_code"] = 2  # avoid
        df = pd.concat([df, synthetic_samples], ignore_index=True)

    # Stop Loss e Take Profit com variação realista para Forex
    # Faixas típicas: 10 a 50 pips (EURUSD: 1 pip = 0.0001)
    # Exemplo: 10 pips = 0.001, 20 pips = 0.002, 50 pips = 0.005
    sl_map = {0: (0.001, 0.002), 1: (0.002, 0.0035), 2: (0.0035, 0.005)}  # conservador, moderado, agressivo
    tp_map = {0: (0.002, 0.004), 1: (0.004, 0.007), 2: (0.007, 0.012)}

    df["stop_loss_pct"] = df["risk_level_code"].apply(lambda x: np.round(np.random.uniform(*sl_map[x]), 4))
    df["take_profit_pct"] = df["risk_level_code"].apply(lambda x: np.round(np.random.uniform(*tp_map[x]), 4))

    # Features adaptadas para MT5/Forex
    features = [
        "capital", "in_position", "drawdown", "atr", "signal", "confidence",
        "recent_losses", "volatility_score", "rolling_loss_ratio", "spread_pct"
    ]
    
    X = df[features]
    y_action = df["action_code"]
    y_risk = df["risk_level_code"]
    y_pos = df["position_size"]
    y_stop = df["stop_loss_pct"]
    y_tp = df["take_profit_pct"]

    X_train, X_test, y_action_train, y_action_test = train_test_split(X, y_action, test_size=0.2, random_state=42)
    _, _, y_risk_train, y_risk_test = train_test_split(X, y_risk, test_size=0.2, random_state=42)
    _, _, y_pos_train, y_pos_test = train_test_split(X, y_pos, test_size=0.2, random_state=42)
    _, _, y_stop_train, y_stop_test = train_test_split(X, y_stop, test_size=0.2, random_state=42)
    _, _, y_tp_train, y_tp_test = train_test_split(X, y_tp, test_size=0.2, random_state=42)

    print(f"📊 Features utilizadas: {features}")
    print(f"📈 Tamanho do dataset: {len(X)} registros")

    return {
        "X_train": X_train,
        "X_test": X_test,
        "y_action_train": y_action_train,
        "y_action_test": y_action_test,
        "y_risk_train": y_risk_train,
        "y_risk_test": y_risk_test,
        "y_pos_train": y_pos_train,
        "y_pos_test": y_pos_test,
        "y_stop_train": y_stop_train,
        "y_stop_test": y_stop_test,
        "y_tp_train": y_tp_train,
        "y_tp_test": y_tp_test
    }
