import pandas as pd
import os
import sys

# Adiciona o diretório raiz ao path para encontrar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from data.utils.preprocess_mt5_data import add_indicators

def process_all_mt5_symbols():
    """Processa todos os símbolos MT5 e combina em um único arquivo"""
    
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
    timeframe = "M15"
    input_dir = "data/raw"
    output_file = "data/processed/market_features_m15.parquet"
    
    all_data = []
    
    for symbol in symbols:
        input_file = os.path.join(input_dir, f"{symbol}_{timeframe}.csv")
        
        if not os.path.exists(input_file):
            print(f"⚠️ Arquivo não encontrado: {input_file}")
            continue
            
        try:
            print(f"🔄 Processando {symbol}...")
            df = pd.read_csv(input_file, parse_dates=["time"])
            
            # Adiciona coluna de símbolo
            df["symbol"] = symbol
            
            # Adiciona indicadores
            df = add_indicators(df)
            
            all_data.append(df)
            print(f"✅ {symbol} processado: {len(df)} registros")
            
        except Exception as e:
            print(f"❌ Erro ao processar {symbol}: {e}")
    
    if all_data:
        # Combina todos os dados
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Salva arquivo combinado
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        combined_df.to_parquet(output_file, index=False)
        
        print(f"\n🎉 Processamento concluído!")
        print(f"📊 Total de registros: {len(combined_df)}")
        print(f"📁 Arquivo salvo: {output_file}")
        print(f"📈 Símbolos processados: {combined_df['symbol'].unique()}")
        
        return combined_df
    else:
        print("❌ Nenhum dado foi processado com sucesso")
        return None

if __name__ == "__main__":
    process_all_mt5_symbols() 