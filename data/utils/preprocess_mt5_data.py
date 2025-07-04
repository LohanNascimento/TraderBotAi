import pandas as pd
import ta
import os


def add_indicators(df):
    # Indicadores de tendência
    df["ema_20"] = ta.trend.EMAIndicator(close=df["close"], window=20).ema_indicator()
    df["ema_50"] = ta.trend.EMAIndicator(close=df["close"], window=50).ema_indicator()
    df["macd"] = ta.trend.MACD(close=df["close"]).macd_diff()

    # Indicadores de momentum
    df["rsi"] = ta.momentum.RSIIndicator(close=df["close"], window=14).rsi()
    df["stoch_k"] = ta.momentum.StochasticOscillator(
        high=df["high"], low=df["low"], close=df["close"]).stoch()

    # Volatilidade
    df["atr"] = ta.volatility.AverageTrueRange(
        high=df["high"], low=df["low"], close=df["close"]).average_true_range()

    # Indicadores de volume (usando tick_volume para MT5)
    df["obv"] = ta.volume.OnBalanceVolumeIndicator(close=df["close"], volume=df["tick_volume"]).on_balance_volume()
    df["volume_sma_20"] = ta.trend.SMAIndicator(close=df["tick_volume"], window=20).sma_indicator()

    # Volatility Stop (usando ATR)
    df["volatility_stop"] = df["close"] - 2 * df["atr"]

    # Volatility Score
    df["volatility_score"] = df["atr"] / df["close"]

    # Adiciona spread como feature (específico do MT5)
    df["spread_pct"] = df["spread"] / df["close"]

    df = df.dropna().reset_index(drop=True)
    return df


def preprocess_and_save(input_file, output_file):
    df = pd.read_csv(input_file, parse_dates=["time"])
    df = add_indicators(df)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_parquet(output_file, index=False)
    print(f"✅ Dados processados salvos em: {output_file}")
    return df


if __name__ == "__main__":
    preprocess_and_save(
        input_file="data/raw/EURUSD_M15.csv",
        output_file="data/processed/market_features_m15.parquet"
    )
