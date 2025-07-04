🧪 Exemplo de uso

python data/utils/fetch_binance_data.py

Isso irá coletar cerca de 180 dias de dados de 15 minutos do par BTC/USDT da Binance e salvar em data/raw/.

🧪 Executar

python data/utils/preprocess_market_data.py

Gera o arquivo data/processed/market_features.parquet com timestamps, OHLCV e indicadores.

models/
└── market_analysis/
    ├── train_market_model.py         # Treinamento do modelo
    ├── model_market.pkl              # Modelo treinado (output)
    ├── market_dataset.py             # Carregamento e rotulagem do dataset (Random Forest)
    ├── lstm_market_dataset.py        # Carregamento e preparação de sequências para LSTM
    ├── train_lstm_market_model.py    # Treinamento ou carregamento de modelo LSTM
    └── evaluate_market_model.py      # Métricas de validação (F1, confusion, etc.)

🧪 Como rodar (Modelo RandomForest Padrão):

python models/market_analysis/train_market_model.py

Esse comando irá:
Treinar um Random Forest com os dados preparados (de `market_dataset.py`).
Imprimir métricas e salvar o modelo em `.pkl`.

🧠 Como usar um Modelo LSTM Pré-Treinado para Análise de Mercado:

1.  **Coloque seu modelo LSTM e scaler nos locais corretos:**
    *   Modelo LSTM (ex: `.h5`): `models/market_analysis/model/lstm_market_model.h5`
    *   Scaler (ex: `MinMaxScaler` salvo com `joblib` como `.pkl`): `models/market_analysis/model/lstm_scaler.pkl`

2.  **Atualize a configuração `config/settings.yaml`:**
    ```yaml
    model_paths:
      # Comente ou remova a linha do market_analysis RandomForest
      # market_analysis: "models/market_analysis/model/model_market.pkl"

      # Adicione os caminhos para o seu modelo LSTM e scaler
      lstm_market_model: "models/market_analysis/model/lstm_market_model.h5"
      lstm_market_scaler: "models/market_analysis/model/lstm_scaler.pkl"

      # ... outros modelos de risco e execução ...

    # (Opcional) Configure os parâmetros do LSTM Wrapper
    lstm_wrapper_params:
      timesteps: 20  # Ajuste para o número de timesteps que seu LSTM espera
      # expected_features: ['open', 'high', 'low', 'close', ...] # Descomente e liste se for diferente do default no wrapper
    ```

3.  **Execute o bot:**
    O `core/logic.py` irá carregar automaticamente o `LSTMModelWrapper` com base nessas configurações.

4.  **(Opcional) Treinar/Re-treinar um modelo LSTM usando os scripts fornecidos:**
    *   Execute `python models/market_analysis/train_lstm_market_model.py`.
    *   Você pode ajustar `TRAIN_NEW = True` no script para treinar um novo modelo ou `TRAIN_NEW = False` para tentar carregar um modelo existente (definido por `MODEL_SAVE_PATH` no script).
    *   O script `lstm_market_dataset.py` é usado por `train_lstm_market_model.py` para preparar os dados.

Esse comando irá:

Treinar um Random Forest com os dados preparados

Imprimir métricas:

Acurácia

F1 Score por classe

Matriz de confusão

Salvar o modelo treinado em .pkl

🧠 O que podemos ajustar depois:
Trocar o modelo por um MLP (rede neural)

Testar diferentes horizontes (future_horizon) e threshold

Normalizar os dados (opcional para Random Forest, essencial para redes)

Usar técnicas de balanceamento se houver desbalanceamento de classes

🔜 Próximo passo
Podemos agora:

Criar o evaluate_market_model.py para testar o modelo salvo com novos dados

Integrar este modelo ao pipeline de decisão no core/logic.py

models/
└── risk_management/
    ├── train_risk_model.py          # Treinamento dos modelos de risco
    ├── risk_dataset.py              # Prepara os dados para treino
    ├── model_risk.pkl               # Modelo treinado (output)
    └── rules_fallback.py            # Regras básicas em caso de falha do modelo

🧪 Executar

python models/risk_management/train_risk_model.py

Isso irá:

Treinar 5 modelos com os dados sintéticos

Imprimir as métricas (classificação e erro médio)

Salvar os arquivos .pkl na pasta models/risk_management/


models/
└── strategy_execution/
    ├── exec_dataset.py              # Geração de dados sintéticos e rótulos
    ├── train_exec_model.py          # Treinamento
    ├── model_exec.pkl               # Modelo treinado
    └── rulebook.py                  # Regras de fallback / explicação

✅ O que esse script faz
Treina o modelo com os dados preparados no exec_dataset.py

Imprime métricas de classificação

Salva o modelo final da cadeia de decisão: model_exec.pkl

🧪 Executar

python models/strategy_execution/train_exec_model.py

backtest/
├── run_backtest.py              # Script principal
├── trader_simulator.py          # Motor de simulação de capital e operações
└── trade_log.csv                # Log de todas as decisões e operações


🧪 Como rodar

python backtest/run_backtest.py

🗂️ Resultados salvos
backtest/trade_log.csv: histórico completo de trades

backtest/equity_curve.csv: evolução do capital ao longo do tempo

🔍 Próximos passos opcionais
Plotar gráfico do equity curve (matplotlib)

Adicionar métricas: win rate, média de lucro, drawdown, etc.

Validar resultados com diferentes períodos e ativos