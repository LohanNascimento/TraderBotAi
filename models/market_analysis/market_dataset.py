import pandas as pd
from sklearn.model_selection import train_test_split

def load_market_dataset(
    file_path="data/processed/market_features_m15.parquet",
    future_horizon=5,
    quantile_threshold=0.1,
    test_size=0.2,
    random_state=42,
    min_volatility_score=None,
    symbols=None
):
    """
    Carrega o dataset de mercado MT5, gera os rótulos usando quantis para balancear
    as classes e divide em treino/teste. Permite filtrar por volatilidade mínima e símbolos específicos.
    """
    df = pd.read_parquet(file_path).copy()
    
    # Filtra por símbolos específicos se fornecido
    if symbols is not None:
        df = df[df["symbol"].isin(symbols)].copy()
        print(f"📊 Filtrando por símbolos: {symbols}")
    
    print(f"📈 Dataset carregado: {len(df)} registros")
    print(f"📊 Símbolos disponíveis: {df['symbol'].unique()}")

    # Cálculo do retorno futuro
    df["future_return"] = (df["close"].shift(-future_horizon) - df["close"]) / df["close"]
    df = df.dropna(subset=["future_return"])

    # Define os limites de quantil para classes de compra e venda
    lower_quantile = df["future_return"].quantile(quantile_threshold)
    upper_quantile = df["future_return"].quantile(1 - quantile_threshold)

    # Rótulo de direção
    df["label"] = 0  # Hold como padrão
    df.loc[df["future_return"] > upper_quantile, "label"] = 1   # Sinal de compra
    df.loc[df["future_return"] < lower_quantile, "label"] = -1  # Sinal de venda

    # Remove os dados que não são sinais claros para focar o treino
    df_filtered = df[df["label"] != 0].copy()

    # Filtro de volatilidade mínima, se especificado
    if min_volatility_score is not None:
        df_filtered = df_filtered[df_filtered["volatility_score"] >= min_volatility_score]

    # Seleção de features (incluindo features específicas do MT5)
    feature_cols = [
        "open", "high", "low", "close", "tick_volume",
        "ema_20", "ema_50", "macd", "rsi", "stoch_k", "atr",
        "obv", "volume_sma_20", "volatility_stop", "volatility_score",
        "spread_pct"  # Feature específica do MT5
    ]
    
    # Remove features que podem não existir
    available_features = [col for col in feature_cols if col in df_filtered.columns]
    missing_features = [col for col in feature_cols if col not in df_filtered.columns]
    
    if missing_features:
        print(f"⚠️ Features não encontradas: {missing_features}")
    
    print(f"✅ Features utilizadas: {available_features}")

    X = df_filtered[available_features]
    y = df_filtered["label"].astype(int)
    volatility_score = df_filtered["volatility_score"].values

    # Divisão treino/teste
    X_train, X_test, y_train, y_test, vol_train, vol_test = train_test_split(
        X, y, volatility_score, test_size=test_size, random_state=random_state, stratify=y
    )

    print(f"📊 Divisão treino/teste: {len(X_train)}/{len(X_test)}")
    print(f"📈 Distribuição de classes (treino): {pd.Series(y_train).value_counts().to_dict()}")
    print(f"📈 Distribuição de classes (teste): {pd.Series(y_test).value_counts().to_dict()}")

    return X_train, X_test, y_train, y_test, vol_train, vol_test
