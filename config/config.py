import yaml
import os

def load_config(path="config/settings.yaml"):
    with open(path, "r") as f:
        config = yaml.safe_load(f)

    # Substitui valores sensíveis com variáveis de ambiente, se presentes
    if "binance" in config:
        config["binance"]["api_key"] = os.getenv("BINANCE_API_KEY", config["binance"].get("api_key", ""))
        config["binance"]["api_secret"] = os.getenv("BINANCE_API_SECRET", config["binance"].get("api_secret", ""))

    return config
