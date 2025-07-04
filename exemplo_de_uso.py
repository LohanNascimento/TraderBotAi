from core.logic import run_autonomous_decision
import numpy as np
import time # Para simular um pequeno atraso

# Lista de features esperada pelo LSTMWrapper (default) e pelo core/logic para o mercado
# Ajuste esta lista se 'expected_features' no seu wrapper ou config for diferente.
EXPECTED_LSTM_FEATURES = [
    'open', 'high', 'low', 'close', 'tick_volume',
    'ema_20', 'ema_50', 'macd', 'rsi', 'stoch_k', 'atr',
    'obv', 'volume_sma_20', 'volatility_stop', 'volatility_score',
    'spread_pct' # Adicionado spread_pct que é esperado
]

def generate_dummy_market_data(base_price=26000):
    """Gera dados de mercado dummy com todas as features esperadas."""
    data = {
        "open": base_price + np.random.uniform(-50, 50),
        "high": base_price + np.random.uniform(0, 100),
        "low": base_price - np.random.uniform(0, 100),
        "close": base_price + np.random.uniform(-50, 50),
        "tick_volume": np.random.randint(500, 2000),
        "ema_20": base_price + np.random.uniform(-30, 30),
        "ema_50": base_price + np.random.uniform(-60, 60),
        "macd": np.random.uniform(-0.005, 0.005),
        "rsi": np.random.uniform(30, 70),
        "stoch_k": np.random.uniform(20, 80),
        "atr": np.random.uniform(0.01, 0.03),
        "obv": np.random.randint(10000, 50000),
        "volume_sma_20": np.random.randint(700, 1500),
        "volatility_stop": base_price - np.random.uniform(50,100), # Exemplo
        "volatility_score": np.random.uniform(0.001, 0.005),      # Exemplo
        "spread_pct": np.random.uniform(0.00005, 0.0002)        # Exemplo spread_pct
    }
    # Garante que high é o mais alto e low o mais baixo
    data["high"] = max(data["high"], data["open"], data["close"])
    data["low"] = min(data["low"], data["open"], data["close"])

    # Adicionar quaisquer features faltantes da lista EXPECTED_LSTM_FEATURES com valor default
    for feat in EXPECTED_LSTM_FEATURES:
        if feat not in data:
            data[feat] = 0.0 # Ou um valor default mais apropriado
    return data

# Estado inicial do trader
current_state = {
    "capital": 10000,
    "in_position": 0,      # 0 = não, 1 = sim (ou poderia ser -1 para short, 1 para long)
    "drawdown": 0.0,
    "time_in_trade": 0,    # Em número de velas/períodos
    "recent_losses": 0,
    "profit_pct": 0.0,
    "symbol": "EURUSD_TEST", # Importante para o LSTMWrapper gerenciar históricos
    "time_since_last_trade": 0 # Adicionado para o modelo de execução
}

# Simular várias iterações para popular o histórico do LSTM
# O número de iterações deve ser pelo menos 'timesteps' (default 20) + algumas extras
num_iterations = 25
timesteps_lstm = 20 # Assumindo o default do wrapper e config

print(f"Simulando {num_iterations} iterações para o símbolo: {current_state['symbol']}")
print("Certifique-se de que o modelo LSTM e o scaler estão nos caminhos corretos especificados em config/settings.yaml")
print("Caminhos esperados (default):")
print("  Modelo: models/market_analysis/model/lstm_market_model.h5")
print("  Scaler: models/market_analysis/model/lstm_scaler.pkl")
print("-" * 30)

for i in range(num_iterations):
    print(f"\n--- Iteração {i + 1}/{num_iterations} ---")

    # Gerar novos dados de mercado para esta iteração
    # Passar o 'symbol' também no market se o wrapper o utilizar, mas 'state' é mais comum
    market_data = generate_dummy_market_data(base_price=26000 + i*10)
    market_data["symbol"] = current_state["symbol"] # Adiciona símbolo aos dados de mercado também

    print(f"Dados de Mercado (vela {i+1}): close={market_data['close']:.2f}, rsi={market_data['rsi']:.2f}")

    # Chamar a lógica de decisão
    # O wrapper LSTM dentro de run_autonomous_decision usará o 'symbol' do 'current_state'
    # para buscar/atualizar o histórico de dados correto.
    decision_output = run_autonomous_decision(market_data, current_state)

    print(f"Decisão: {decision_output.get('final_decision', 'N/A')}")
    print(f"  Sinal LSTM: {decision_output.get('signal', 'N/A')}, Confiança LSTM: {decision_output.get('confidence', 0.0):.4f}")
    print(f"  Tamanho Posição: {decision_output.get('position_size', 'N/A')}")

    # Atualizar o estado (simulação básica)
    if current_state["in_position"]:
        current_state["time_in_trade"] += 1
        current_state["profit_pct"] += np.random.uniform(-0.005, 0.005) # Simula variação de lucro
    else:
        current_state["time_in_trade"] = 0
        current_state["time_since_last_trade"] +=1

    if decision_output.get('final_decision') == 'buy' and not current_state["in_position"]:
        current_state["in_position"] = 1
        current_state["profit_pct"] = 0.0
        current_state["time_since_last_trade"] = 0
        print("  AÇÃO: Entrou em Compra (simulado)")
    elif decision_output.get('final_decision') == 'sell' and current_state["in_position"]:
        current_state["in_position"] = 0
        print(f"  AÇÃO: Saiu da Posição (simulado) com lucro/perda: {current_state['profit_pct']:.4f}")
        current_state["profit_pct"] = 0.0 # Reset profit_pct ao sair

    # Adiciona um pequeno delay para não sobrecarregar o console e simular tempo real
    # time.sleep(0.1)

    if i < timesteps_lstm -1 : # O wrapper retorna 0,0 antes de ter dados suficientes
        if decision_output.get('signal', 'N/A') != 0 or decision_output.get('confidence', 0.0) != 0.0:
             print(f"⚠️ AVISO: Wrapper LSTM retornou sinal/confiança não nulos ANTES de ter {timesteps_lstm} timesteps. Verifique a lógica do wrapper.")
    elif i == timesteps_lstm -1 :
        print(f"🎉 Histórico LSTM para '{current_state['symbol']}' deve estar completo agora ({timesteps_lstm} amostras). Próximas predições usarão o modelo.")


print("-" * 30)
print("Simulação de exemplo concluída.")
print("Verifique se os sinais e confianças do LSTM parecem razoáveis após as primeiras ~20 iterações.")
print("Se ocorrerem erros, verifique os logs e os caminhos dos arquivos do modelo/scaler.")
