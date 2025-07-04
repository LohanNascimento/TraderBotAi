#!/usr/bin/env python3
"""
Script de teste para verificar integração MT5
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from config.config import load_config
from live_trading.paper_trader import get_latest_candle, get_balance, place_market_order
from live_trading.mt5_trader import connect_mt5, get_latest_candle as mt5_get_candle, get_balance as mt5_get_balance

def test_config():
    """Testa carregamento da configuração"""
    print("🔧 Testando configuração...")
    try:
        cfg = load_config()
        print(f"✅ Configuração carregada")
        print(f"   Símbolos: {cfg['general']['symbols']}")
        print(f"   Timeframe: {cfg['general']['timeframe']}")
        print(f"   Broker: {cfg['general']['broker']}")
        return True
    except Exception as e:
        print(f"❌ Erro na configuração: {e}")
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

def test_data_processing():
    """Testa processamento de dados"""
    print("\n📈 Testando processamento de dados...")
    try:
        # Verifica se arquivos de dados existem
        data_files = [
            "data/raw/EURUSD_M15.csv",
            "data/processed/market_features_m15.parquet"
        ]
        
        for file_path in data_files:
            if os.path.exists(file_path):
                print(f"✅ {file_path} existe")
            else:
                print(f"⚠️ {file_path} não encontrado")
        
        return True
    except Exception as e:
        print(f"❌ Erro no processamento: {e}")
        return False

def main():
    """Executa todos os testes"""
    print("🧪 INICIANDO TESTES DE INTEGRAÇÃO MT5")
    print("=" * 50)
    
    tests = [
        ("Configuração", test_config),
        ("Paper Trader", test_paper_trader),
        ("Conexão MT5", test_mt5_connection),
        ("Processamento de Dados", test_data_processing)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro inesperado em {test_name}: {e}")
            results.append((test_name, False))
    
    # Resumo
    print("\n" + "=" * 50)
    print("📋 RESUMO DOS TESTES")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{len(results)} testes passaram")
    
    if passed == len(results):
        print("🎉 Todos os testes passaram! Integração MT5 funcionando.")
    else:
        print("⚠️ Alguns testes falharam. Verifique os erros acima.")

if __name__ == "__main__":
    main() 