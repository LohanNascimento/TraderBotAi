import MetaTrader5 as mt5
import pandas as pd
import time
from config.config import load_config
from datetime import datetime
import MetaTrader5 as mt5
from live_trading.mt5_api import connect as connect_mt5, disconnect as disconnect_mt5, get_latest_candle, get_config

def get_lot_limits(symbol):
    info = mt5.symbol_info(symbol)
    if info is None:
        return 0.01, 100.0, 0.01  # defaults
    return info.volume_min, info.volume_max, info.volume_step

def place_market_order(symbol: str, side: str, quantity: float):
    """Executa ordem de mercado no MT5"""
    if not connect_mt5():
        return None
    
    cfg = get_config()
    mt5_config = cfg["mt5"]
    
    # Obtenha o preço de mercado atual
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"❌ Erro ao obter preço do símbolo {symbol}")
        return None

    if side == "BUY":
        price = tick.ask
    else:
        price = tick.bid

    # Determina tipo de ordem
    order_type = mt5.ORDER_TYPE_BUY if side == "BUY" else mt5.ORDER_TYPE_SELL

    # Ajusta o volume para os limites do ativo
    min_lot, max_lot, lot_step = get_lot_limits(symbol)
    # Corrige para múltiplo do step
    adj_qty = max(min_lot, min(max_lot, round(quantity / lot_step) * lot_step))
    if (adj_qty - min_lot) % lot_step != 0:
        # Garante múltiplo exato
        adj_qty = min_lot + round((adj_qty - min_lot) / lot_step) * lot_step
    adj_qty = round(adj_qty, len(str(lot_step).split('.')[-1]))
    if adj_qty < min_lot or adj_qty > max_lot:
        print(f"❌ Volume ajustado ({adj_qty}) fora dos limites do ativo {symbol} (min: {min_lot}, max: {max_lot}, step: {lot_step})")
        return None

    # Obtém os modos de preenchimento permitidos para o símbolo
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"Erro: Não foi possível obter informações do símbolo {symbol}")
        return None
    allowed_filling_modes = symbol_info.filling_mode

    # Lista de modos suportados pelo MetaTrader 5
    supported_filling_modes = [
        mt5.ORDER_FILLING_FOK,
        mt5.ORDER_FILLING_IOC,
        mt5.ORDER_FILLING_RETURN
    ]
    # Seleciona o primeiro modo permitido pelo símbolo e suportado pelo MT5
    type_filling = None
    for mode in supported_filling_modes:
        if allowed_filling_modes & mode:
            type_filling = mode
            break
    if type_filling is None:
        print(f"❌ Nenhum modo de preenchimento suportado encontrado para {symbol}. Consulte a corretora.")
        disconnect_mt5()
        return None

    # Obtém o tamanho do ponto do ativo
    point = mt5.symbol_info(symbol).point if mt5.symbol_info(symbol) else 0.0

    # --- NOVO BLOCO: lê os percentuais do modelo ---
    import json
    try:
        with open("d:/forex_trader_ai/last_decision.json", "r") as f:
            decision = json.load(f)
        stop_loss_pct = decision.get("stop_loss_pct", 0.0)
        take_profit_pct = decision.get("take_profit_pct", 0.0)
    except Exception as e:
        print(f"Erro ao ler last_decision.json: {e}")
        stop_loss_pct = 0.0
        take_profit_pct = 0.0

    # Calcula SL e TP conforme o lado da ordem
    if side == "BUY":
        sl = price * (1 - stop_loss_pct) if stop_loss_pct else 0.0
        tp = price * (1 + take_profit_pct) if take_profit_pct else 0.0
    else:
        sl = price * (1 + stop_loss_pct) if stop_loss_pct else 0.0
        tp = price * (1 - take_profit_pct) if take_profit_pct else 0.0

    # Prepara ordem
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": adj_qty,
        "type": order_type,
        "price": price,  # Corrigido: preço de mercado
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 234000,
        "comment": "python order",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": type_filling,
    }
    
    try:
        result = mt5.order_send(request)
        if result is None:
            print("❌ Erro: mt5.order_send retornou None. Verifique conexão, símbolo e parâmetros.")
            print("Detalhe do erro MT5:", mt5.last_error())
            return None
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"❌ Erro na ordem: {result.comment}")
            return None
        print(f"✅ Ordem executada: {side} {adj_qty} {symbol}")
        return {
            "status": "FILLED",
            "order": result.order,
            "volume": result.volume,
            "price": result.price
        }
        
    except Exception as e:
        print(f"❌ Erro ao executar ordem: {e}")
        return None

def get_balance(asset="USD"):
    """Obtém saldo da conta MT5"""
    if not connect_mt5():
        return 0.0
    
    try:
        account_info = mt5.account_info()
        if account_info is None:
            print("❌ Erro ao obter informações da conta")
            return 0.0
        
        # MT5 retorna saldo em moeda da conta (geralmente USD)
        return float(account_info.balance)
        
    except Exception as e:
        print(f"❌ Erro ao obter saldo: {e}")
        return 0.0

def get_positions(symbol=None):
    """Obtém posições abertas"""
    if not connect_mt5():
        return []
    
    try:
        positions = mt5.positions_get(symbol=symbol)
        if positions is None:
            return []
        
        return [
            {
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": "BUY" if pos.type == mt5.POSITION_TYPE_BUY else "SELL",
                "price_open": pos.price_open,
                "price_current": pos.price_current,
                "profit": pos.profit
            }
            for pos in positions
        ]
        
    except Exception as e:
        print(f"❌ Erro ao obter posições: {e}")
        return []

def check_spread(symbol: str, max_spread: float = None) -> bool:
    """Verifica se o spread_pct está aceitável"""
    if max_spread is None:
        cfg = get_config()
        max_spread = cfg["mt5"]["max_spread"]
    
    candle = get_latest_candle(symbol)
    if candle is None:
        return False
    
    current_spread_pct = candle["spread"] / candle["close"] if candle["close"] != 0 else 0
    return current_spread_pct <= max_spread