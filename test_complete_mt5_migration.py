#!/usr/bin/env python3
"""
Script de teste completo para verificar migração MT5
"""

import sys
import os
import time
sys.path.append(os.path.dirname(__file__))

from config.config import load_config
from live_trading.paper_trader import get_latest_candle, get_balance, place_market_order
from live_trading.mt5_trader import connect_mt5, get_latest_candle as mt5_get_candle, get_balance as mt5_get_balance
from core.logic import run_autonomous_decision
from core.signals import add_indicators
import pandas as pd

def test_configuration():
    """Testa configuração MT5"""
    print("🔧 Testando configuração...")
    try:
        cfg = load_config()
        print(f"✅ Configuração carregada")
        print(f"   Símbolos: {cfg['general']['symbols']}")
        print(f"   Timeframe: {cfg['general']['timeframe']}")
        print(f"   Broker: {cfg['general']['broker']}")
        print(f"   Dados: {cfg['general']['data_path']}")
        
        # Verifica se é MT5
        if cfg['general']['broker'] != 'MT5':
            print("⚠️ Configuração não está para MT5")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
        return False

def test_data_files():
    """Testa arquivos de dados MT5"""
    print("\n📊 Testando arquivos de dados...")
    try:
        cfg = load_config()
        
        # Verifica arquivos individuais
        symbols = cfg["general"]["symbols"]
        timeframe = cfg["general"]["timeframe"]
        
        individual_files = []
        for symbol in symbols:
            file_path = f"data/raw/{symbol}_{timeframe}.csv"
            if os.path.exists(file_path):
                print(f"✅ {file_path}")
                individual_files.append(file_path)
            else:
                print(f"⚠️ {file_path} não encontrado")
        
        # Verifica arquivo combinado
        combined_file = cfg["general"]["data_path"]
        if os.path.exists(combined_file):
            print(f"✅ {combined_file}")
            # Testa leitura
            df = pd.read_parquet(combined_file)
            print(f"   📈 Registros: {len(df)}")
            print(f"   📊 Símbolos: {df['symbol'].unique()}")
            print(f"   🔧 Colunas: {list(df.columns)}")
        else:
            print(f"⚠️ {combined_file} não encontrado")
            return False
            
        return True
    except Exception as e:
        print(f"❌ Erro nos dados: {e}")
        return False

def test_models():
    """Testa carregamento dos modelos"""
    print("\n🧠 Testando modelos...")
    try:
        cfg = load_config()
        
        model_files = [
            ("Market Analysis", cfg["model_paths"]["market_analysis"]),
            ("Risk Action", cfg["model_paths"]["risk_action"]),
            ("Risk Level", cfg["model_paths"]["risk_level"]),
            ("Position Size", cfg["model_paths"]["position_size"]),
            ("Stop Loss", cfg["model_paths"]["stop_loss"]),
            ("Take Profit", cfg["model_paths"]["take_profit"]),
            ("Strategy Execution", cfg["model_paths"]["strategy_exec"]),
            ("Execution Labels", cfg["model_paths"]["exec_labels"])
        ]
        
        for name, path in model_files:
            if os.path.exists(path):
                print(f"✅ {name}: {path}")
            else:
                print(f"❌ {name}: {path} não encontrado")
                return False
                
        return True
    except Exception as e:
        print(f"❌ Erro nos modelos: {e}")
        return False

def test_paper_trader():
    """Testa paper trader adaptado para MT5"""
    print("\n📊 Testando Paper Trader (MT5)...")
    try:
        # Testa obtenção de candle
        symbol = "EURUSD"
        candle = get_latest_candle(symbol, "M15")
        print(f"✅ Candle obtido para {symbol}:")
        print(f"   Close: {candle['close']:.5f}")
        print(f"   Volume: {candle['volume']}")
        print(f"   Spread: {candle.get('spread', 'N/A')}")
        
        # Testa saldo
        balance = get_balance("USD")
        print(f"✅ Saldo USD: ${balance:.2f}")
        
        # Testa simulação de ordem
        order = place_market_order(symbol, "BUY", 0.01)
        if order:
            print(f"✅ Ordem simulada: {order['status']}")
        
        return True
    except Exception as e:
        print(f"❌ Erro no paper trader: {e}")
        return False

def test_mt5_connection():
    """Testa conexão real com MT5"""
    print("\n🔌 Testando conexão MT5...")
    try:
        if connect_mt5():
            # Testa obtenção de candle real
            symbol = "EURUSD"
            candle = mt5_get_candle(symbol, "M15")
            if candle:
                print(f"✅ Candle MT5 obtido para {symbol}:")
                print(f"   Close: {candle['close']:.5f}")
                print(f"   Volume: {candle['volume']}")
                print(f"   Spread: {candle['spread']}")
            
            # Testa saldo real
            balance = mt5_get_balance("USD")
            print(f"✅ Saldo MT5 USD: ${balance:.2f}")
            
            return True
        else:
            print("❌ Falha na conexão MT5")
            return False
    except Exception as e:
        print(f"❌ Erro na conexão MT5: {e}")
        return False

def test_core_logic():
    """Testa lógica de decisão com dados MT5"""
    print("\n🧠 Testando lógica de decisão...")
    try:
        # Simula dados de mercado MT5 (incluindo spread_pct)
        market_data = {
            "open": 1.1350,
            "high": 1.1360,
            "low": 1.1340,
            "close": 1.1355,
            "tick_volume": 1000,
            "spread": 8.0,
            "real_volume": 1000,
            "ema_20": 1.1352,
            "ema_50": 1.1348,
            "macd": 0.0002,
            "rsi": 55.0,
            "stoch_k": 60.0,
            "atr": 0.0015,
            "obv": 50000,
            "volume_sma_20": 950,
            "volatility_stop": 1.1325,
            "volatility_score": 0.0013,
            "spread_pct": 0.0001  # Feature específica MT5
        }
        
        # Simula estado
        state = {
            "capital": 10000,
            "in_position": False,
            "entry_price": 0.0,
            "drawdown": 0.02,
            "recent_losses": 1,
            "time_in_trade": 0,
            "profit_pct": 0.0
        }
        
        # Executa decisão
        decision = run_autonomous_decision(market_data, state)
        print(f"✅ Decisão gerada:")
        print(f"   Final: {decision['final_decision']}")
        print(f"   Signal: {decision['signal']}")
        print(f"   Confidence: {decision['confidence']:.3f}")
        print(f"   Position Size: {decision['position_size']:.3f}")
        
        return True
    except Exception as e:
        print(f"❌ Erro na lógica: {e}")
        return False

def test_signals():
    """Testa geração de indicadores"""
    print("\n📈 Testando indicadores...")
    try:
        # Cria dados de teste
        data = {
            'open': [1.1350, 1.1355, 1.1360],
            'high': [1.1360, 1.1365, 1.1370],
            'low': [1.1340, 1.1345, 1.1350],
            'close': [1.1355, 1.1360, 1.1365],
            'volume': [1000, 1100, 1200]
        }
        df = pd.DataFrame(data)
        
        # Adiciona indicadores
        df_with_indicators = add_indicators(df)
        print(f"✅ Indicadores adicionados:")
        print(f"   Colunas: {list(df_with_indicators.columns)}")
        print(f"   EMA20: {df_with_indicators['ema_20'].iloc[-1]:.5f}")
        print(f"   RSI: {df_with_indicators['rsi'].iloc[-1]:.2f}")
        
        return True
    except Exception as e:
        print(f"❌ Erro nos indicadores: {e}")
        return False

def test_integration():
    """Testa integração completa"""
    print("\n🔄 Testando integração completa...")
    try:
        # Simula um ciclo completo
        symbol = "EURUSD"
        
        # 1. Obtém dados
        candle = get_latest_candle(symbol, "M15")
        print(f"✅ Dados obtidos: {candle['close']:.5f}")
        
        # 2. Adiciona indicadores
        df = pd.DataFrame([candle])
        df_with_indicators = add_indicators(df)
        latest = df_with_indicators.iloc[-1].to_dict()
        
        # 3. Garante que todas as features necessárias estão presentes
        required_features = [
            'open', 'high', 'low', 'close', 'tick_volume', 'spread', 'real_volume',
            'ema_20', 'ema_50', 'macd', 'rsi', 'stoch_k', 'atr', 'obv', 
            'volume_sma_20', 'volatility_stop', 'volatility_score', 'spread_pct'
        ]
        
        # Adiciona features que podem estar faltando
        for feature in required_features:
            if feature not in latest:
                if feature == 'spread_pct':
                    latest[feature] = latest.get('spread', 0) / latest['close'] if latest['close'] > 0 else 0.0001
                elif feature == 'tick_volume':
                    latest[feature] = latest.get('volume', 1000)
                elif feature == 'real_volume':
                    latest[feature] = latest.get('volume', 1000)
                elif feature == 'spread':
                    latest[feature] = 8.0  # Valor padrão MT5
                else:
                    latest[feature] = 0.0
        
        print(f"✅ Indicadores calculados")
        print(f"   Features: {len(latest)}")
        
        # 4. Simula estado
        state = {
            "capital": 10000,
            "in_position": False,
            "entry_price": 0.0,
            "drawdown": 0.0,
            "recent_losses": 0,
            "time_in_trade": 0,
            "profit_pct": 0.0
        }
        
        # 5. Executa decisão
        decision = run_autonomous_decision(latest, state)
        print(f"✅ Decisão: {decision['final_decision']}")
        
        # 6. Simula ordem se necessário
        if decision['final_decision'] == 'buy':
            order = place_market_order(symbol, "BUY", 0.01)
            if order:
                print(f"✅ Ordem simulada: {order['status']}")
        
        return True
    except Exception as e:
        print(f"❌ Erro na integração: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 TESTE COMPLETO DE MIGRAÇÃO MT5")
    print("=" * 60)
    
    tests = [
        ("Configuração", test_configuration),
        ("Arquivos de Dados", test_data_files),
        ("Modelos", test_models),
        ("Paper Trader", test_paper_trader),
        ("Conexão MT5", test_mt5_connection),
        ("Lógica de Decisão", test_core_logic),
        ("Indicadores", test_signals),
        ("Integração Completa", test_integration)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Pausa entre testes
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📋 RESUMO FINAL DOS TESTES")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("\n🎉 MIGRAÇÃO MT5 CONCLUÍDA COM SUCESSO!")
        print("✅ Todos os componentes estão funcionando")
        print("✅ Sistema pronto para operar com MT5")
        print("\n🚀 Próximos passos:")
        print("   1. Configure suas credenciais MT5 em config/settings.yaml")
        print("   2. Execute: python main.py")
        print("   3. Use comandos Telegram para controlar o bot")
    else:
        print("\n⚠️ ALGUNS TESTES FALHARAM")
        print("🔧 Verifique os erros acima e corrija antes de prosseguir")
        
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 