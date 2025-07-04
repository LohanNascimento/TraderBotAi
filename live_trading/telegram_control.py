import threading
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from live_trading.mt5_trader import get_balance
from live_trading.mt5_api import get_latest_candle
import json
import os

# Placeholders - insira seu token e user_id
TELEGRAM_TOKEN = '7994947765:AAFzB-qZXYBLrbGTPiBdAqlT23ELvz0umCs'
AUTHORIZED_USER_IDS = [123456789, -1002660130039]  # Substitua pelo seu user_id e/ou id do grupo

# Teclado de comandos
COMMAND_KEYBOARD = ReplyKeyboardMarkup(
    [
        ["/status", "/pause"],
        ["/resume", "/stop"]
    ],
    resize_keyboard=True
)

# Função para checar autorização
def is_authorized(update: Update):
    return (
        update.effective_user.id in AUTHORIZED_USER_IDS or
        update.effective_chat.id in AUTHORIZED_USER_IDS
    )

# Variáveis globais de controle
paused = False
running = True

# Funções de controle para o loop principal acessar

def is_paused():
    global paused
    return paused

def is_running():
    global running
    return running

def set_paused(value: bool):
    global paused
    paused = value

def set_running(value: bool):
    global running
    running = value

# Funções de resposta aos comandos
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Acesso negado.", reply_markup=COMMAND_KEYBOARD)
        return
    await update.message.reply_text(
        "🤖 Bot de trading pronto para comandos! Use os botões abaixo ou digite um comando.",
        reply_markup=COMMAND_KEYBOARD
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Acesso negado.", reply_markup=COMMAND_KEYBOARD)
        return

    # Carrega estados dos arquivos JSON
    def load_json(path, default={}):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except:
            return default

    positions = load_json("position_state.json")
    last_decision = load_json("last_decision.json")

    # Obtém saldo USD
    usd_balance = get_balance("USD")

    open_positions = []
    total_pnl = 0.0

    def format_time(minutes):
        if not minutes or not isinstance(minutes, (int, float)):
            return "-"
        h = int(minutes // 60)
        m = int(minutes % 60)
        if h > 0:
            return f"{h}h {m}min"
        return f"{m}min"

    for symbol, pos in positions.items():
        if pos["in_position"]:
            entry_price = pos["entry_price"]
            time_in_trade = pos["time_in_trade"]
            profit_pct = pos["profit_pct"] * 100
            # Quantidade pode não estar presente
            qty = pos.get("quantity", 1)
            open_positions.append(
                f"• {symbol}: {qty:.4f} @ ${entry_price:.5f} | Tempo: {format_time(time_in_trade)} | Lucro: {profit_pct:.2f}%"
            )
            # Não calcula P&L em USD sem preço atual e quantidade

    # Monta mensagem de status
    status_msg = f"📊 **STATUS DO BOT (MT5)**\n\n"
    status_msg += f"🔄 **Estado**: {'⏸️ PAUSADO' if paused else '▶️ RODANDO'}\n"
    status_msg += f"💰 **Saldo USD**: ${usd_balance:.2f}\n"

    if open_positions:
        status_msg += f"\n📈 **Posições Abertas**:\n"
        status_msg += "\n".join(open_positions)
    else:
        status_msg += f"\n📈 **Posições Abertas**: Nenhuma"

    # Última decisão do modelo
    if last_decision:
        status_msg += "\n\n🧠 **Última decisão do modelo**:\n"
        status_msg += f"Ação: {last_decision.get('final_decision', '-')} | Confiança: {last_decision.get('confidence', 0)*100:.2f}%"

    await update.message.reply_text(status_msg, parse_mode='Markdown', reply_markup=COMMAND_KEYBOARD)

async def pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Acesso negado.", reply_markup=COMMAND_KEYBOARD)
        return
    set_paused(True)
    await update.message.reply_text("⏸️ Bot PAUSADO. Não serão feitas novas operações.", reply_markup=COMMAND_KEYBOARD)

async def resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Acesso negado.", reply_markup=COMMAND_KEYBOARD)
        return
    set_paused(False)
    await update.message.reply_text("▶️ Bot RETOMADO. Operações liberadas.", reply_markup=COMMAND_KEYBOARD)

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        await update.message.reply_text("Acesso negado.", reply_markup=COMMAND_KEYBOARD)
        return
    set_running(False)
    await update.message.reply_text("🛑 Bot será encerrado.", reply_markup=COMMAND_KEYBOARD)

# Função para enviar mensagens automáticas do bot para o usuário
async def send_telegram_message(text):
    from telegram import Bot
    bot = Bot(token=TELEGRAM_TOKEN)
    for chat_id in AUTHORIZED_USER_IDS:
        await bot.send_message(chat_id=chat_id, text=text, reply_markup=COMMAND_KEYBOARD)

# Thread para rodar o bot do Telegram
async def telegram_main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("pause", pause))
    app.add_handler(CommandHandler("resume", resume))
    app.add_handler(CommandHandler("stop", stop))
    print("🤖 Telegram control rodando...")
    await app.run_polling()

def start_telegram_thread():
    import asyncio
    import nest_asyncio
    nest_asyncio.apply()
    threading.Thread(target=lambda: asyncio.run(telegram_main()), daemon=True).start()