# 🚀 Guia de Migração para MetaTrader 5 (MT5)

## 📋 Visão Geral

Este guia documenta a migração completa do sistema de trading AI de Binance para MetaTrader 5 (MT5), incluindo todas as mudanças necessárias em configuração, dados, modelos e execução.

## 🔧 Fases da Migração

### ✅ Fase 1: Configuração e Dados
- [x] Configuração MT5 em `config/settings.yaml`
- [x] Adaptação de scripts de dados para formato MT5
- [x] Processamento de múltiplos símbolos
- [x] Criação de arquivo combinado parquet

### ✅ Fase 2: Live Trading
- [x] Módulo MT5 (`live_trading/mt5_trader.py`)
- [x] Adaptação do paper trader
- [x] Integração com bot principal
- [x] Controle via Telegram

### ✅ Fase 3: Modelos
- [x] Adaptação de datasets para MT5
- [x] Retreinamento de modelos
- [x] Atualização da lógica central
- [x] Suporte a features específicas MT5

## 📁 Estrutura de Arquivos

```
crypto_trader_ai/
├── config/
│   ├── settings.yaml          # ✅ Configuração MT5
│   └── config.py              # ✅ Carregador de configuração
├── data/
│   ├── raw/                   # ✅ Dados MT5 CSV
│   │   ├── EURUSD_M15.csv
│   │   ├── GBPUSD_M15.csv
│   │   ├── USDJPY_M15.csv
│   │   └── AUDUSD_M15.csv
│   ├── processed/
│   │   └── market_features_m15.parquet  # ✅ Dados combinados
│   └── utils/
│       ├── fetch_mt5_data.py           # ✅ Busca dados MT5
│       ├── preprocess_mt5_data.py      # ✅ Pré-processamento
│       └── process_all_mt5_data.py     # ✅ Processa todos os símbolos
├── live_trading/
│   ├── mt5_trader.py          # ✅ Módulo MT5
│   ├── paper_trader.py        # ✅ Adaptado para MT5
│   ├── trader_bot.py          # ✅ Integração MT5
│   └── telegram_control.py    # ✅ Mensagens MT5
├── models/
│   ├── market_analysis/       # ✅ Dataset MT5
│   ├── risk_management/       # ✅ Dataset MT5
│   └── strategy_execution/    # ✅ Dataset MT5
├── core/
│   ├── logic.py               # ✅ Lógica MT5
│   └── signals.py             # ✅ Indicadores
└── test_complete_mt5_migration.py  # ✅ Teste completo
```

## ⚙️ Configuração Necessária

### 1. Configuração MT5 em `config/settings.yaml`

```yaml
general:
  broker: "MT5"
  symbols: ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"]
  timeframe: "M15"
  data_path: "data/processed/market_features_m15.parquet"
  base_currency: "USD"
  initial_capital: 10000

mt5:
  server: "seu_broker"
  login: seu_login
  password: "sua_senha"
  symbol_prefix: ""
  symbol_suffix: ""
```

### 2. Instalação de Dependências

```bash
pip install MetaTrader5 pandas numpy scikit-learn
```

## 📊 Processamento de Dados

### 1. Baixar Dados MT5

```bash
python data/utils/fetch_mt5_data.py
```

### 2. Processar Dados

```bash
python data/utils/process_all_mt5_data.py
```

### 3. Verificar Dados

```bash
python -c "
import pandas as pd
df = pd.read_parquet('data/processed/market_features_m15.parquet')
print(f'Registros: {len(df)}')
print(f'Símbolos: {df.symbol.unique()}')
print(f'Colunas: {list(df.columns)}')
"
```

## 🧠 Treinamento de Modelos

### 1. Retreinar Todos os Modelos

```bash
python retrain_all_models_mt5.py
```

### 2. Verificar Modelos

```bash
python -c "
from config.config import load_config
cfg = load_config()
import os
for name, path in cfg['model_paths'].items():
    print(f'{name}: {"✅" if os.path.exists(path) else "❌"} {path}')
"
```

## 🧪 Testes

### 1. Teste Completo

```bash
python test_complete_mt5_migration.py
```

### 2. Teste de Integração MT5

```bash
python test_mt5_integration.py
```

## 🚀 Execução

### 1. Paper Trading

```bash
python main.py --mode paper
```

### 2. Live Trading (MT5)

```bash
python main.py --mode live
```

### 3. Backtest

```bash
python backtest/run_backtest.py
```

## 📱 Controle via Telegram

### Comandos Disponíveis

- `/start` - Inicia o bot
- `/status` - Status atual
- `/balance` - Saldo da conta
- `/positions` - Posições abertas
- `/start_trading` - Inicia trading
- `/stop_trading` - Para trading
- `/paper_mode` - Modo paper trading
- `/live_mode` - Modo live trading

## 🔍 Monitoramento

### 1. Logs

- `paper_trade_log.csv` - Log de paper trading
- `last_decision.json` - Última decisão tomada
- `paper_state.json` - Estado atual

### 2. Dashboard

```bash
python dashboard/app.py
```

Acesse: http://localhost:5000

## ⚠️ Pontos de Atenção

### 1. Credenciais MT5
- Nunca commite credenciais no Git
- Use variáveis de ambiente ou arquivo `.env`
- Configure corretamente servidor, login e senha

### 2. Símbolos MT5
- Verifique se os símbolos existem no seu broker
- Ajuste prefix/suffix conforme necessário
- Teste conectividade antes de operar

### 3. Timeframes
- Sistema configurado para M15
- Ajuste conforme sua estratégia
- Verifique disponibilidade no broker

### 4. Capital e Risk Management
- Configure capital inicial adequado
- Ajuste position sizing
- Configure stop loss e take profit

## 🔧 Troubleshooting

### Problema: Conexão MT5 Falha
```bash
# Verificar se MT5 está instalado
python -c "import MetaTrader5; print('MT5 OK')"

# Testar conexão
python test_mt5_integration.py
```

### Problema: Dados Não Carregam
```bash
# Verificar arquivos
ls -la data/raw/
ls -la data/processed/

# Reprocessar dados
python data/utils/process_all_mt5_data.py
```

### Problema: Modelos Não Carregam
```bash
# Verificar modelos
python -c "
from config.config import load_config
cfg = load_config()
import os
for name, path in cfg['model_paths'].items():
    print(f'{name}: {os.path.exists(path)}')
"

# Retreinar modelos
python retrain_all_models_mt5.py
```

## 📈 Próximos Passos

1. **Configurar Credenciais MT5**
   - Editar `config/settings.yaml`
   - Testar conexão

2. **Executar Testes**
   - `python test_complete_mt5_migration.py`
   - Corrigir erros se houver

3. **Paper Trading**
   - `python main.py --mode paper`
   - Monitorar performance

4. **Live Trading**
   - Configurar Telegram
   - `python main.py --mode live`
   - Usar comandos Telegram

## 🎯 Checklist Final

- [ ] Configuração MT5 em `settings.yaml`
- [ ] Dados MT5 baixados e processados
- [ ] Modelos retreinados com dados MT5
- [ ] Teste completo passou
- [ ] Paper trading funcionando
- [ ] Conexão MT5 testada
- [ ] Telegram configurado
- [ ] Capital e risk management configurados

## 📞 Suporte

Se encontrar problemas:

1. Execute `python test_complete_mt5_migration.py`
2. Verifique logs de erro
3. Consulte este guia
4. Verifique configurações MT5

---

**🎉 Parabéns! Sua migração para MT5 está completa!** 