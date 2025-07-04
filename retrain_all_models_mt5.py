#!/usr/bin/env python3
"""
Script para retreinar todos os modelos com dados MT5
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

# Adiciona os caminhos dos módulos
sys.path.append(os.path.join(os.path.dirname(__file__), 'models', 'market_analysis'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'models', 'risk_management'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'models', 'strategy_execution'))

from models.market_analysis.train_market_model import train_market_model
from models.risk_management.train_risk_model import train_and_save_risk_models
from models.strategy_execution.train_exec_model import train_and_save_exec_model
from config.config import load_config

def main():
    """Retreina todos os modelos com dados MT5"""
    print("🔄 Retreinando todos os modelos com dados MT5...")
    
    try:
        # Carrega configuração
        cfg = load_config()
        print(f"✅ Configuração carregada")
        print(f"   Dados: {cfg['general']['data_path']}")
        
        # 1. Modelo de Análise de Mercado
        print("\n🧠 Treinando modelo de análise de mercado...")
        train_market_model()
        
        # 2. Modelos de Gerenciamento de Risco
        print("\n🛡️ Treinando modelos de gerenciamento de risco...")
        train_and_save_risk_models()
        
        # 3. Modelo de Execução de Estratégia
        print("\n⚡ Treinando modelo de execução de estratégia...")
        train_and_save_exec_model()
        
        print("\n🎉 Todos os modelos foram retreinados com sucesso!")
        print("✅ Modelos atualizados com dados MT5")
        print("✅ Feature 'spread_pct' incluída")
        
    except Exception as e:
        print(f"❌ Erro durante retreinamento: {e}")
        return False
        
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 