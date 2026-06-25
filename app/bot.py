import logging
import re

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import settings
from app.agents.chat_agent import ChatAgent

logger = logging.getLogger(__name__)

chat_contexts: dict[int, list[dict]] = {}
_bot_app: Application | None = None

MAX_TELEGRAM_MSG = 4000

_agent = ChatAgent()


def _format_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    return text


def _render_table(rows: list[list[str]]) -> str:
    clean = [[c.replace("**", "") for c in row] for row in rows]
    col_count = max(len(r) for r in clean)
    widths = []
    for col_idx in range(col_count):
        col_vals = [r[col_idx] if col_idx < len(r) else "" for r in clean]
        widths.append(max(len(v) for v in col_vals))

    lines = []
    for i, row in enumerate(clean):
        cells = [row[ci] if ci < len(row) else "" for ci in range(col_count)]
        padded = [cells[ci].ljust(widths[ci]) for ci in range(col_count)]
        line = "  ".join(padded)
        if i == 0:
            line = "<b>" + line + "</b>"
        lines.append(line)
    return "<pre>" + "\n".join(lines) + "</pre>"


def _format_telegram(text: str) -> str:
    lines = text.split("\n")
    result = []
    in_table = False
    table_lines = []

    for line in lines:
        is_table_row = bool(re.match(r"^\|.+\|$", line.strip()))
        if is_table_row:
            cells = [c.strip() for c in line.strip().split("|")[1:-1]]
            if len(cells) > 0 and all(re.match(r"^-+$", c) for c in cells):
                continue
            if not in_table:
                in_table = True
                table_lines = [cells]
            else:
                table_lines.append(cells)
        else:
            if in_table:
                result.append(_render_table(table_lines))
                in_table = False
                table_lines = []
            result.append(_format_inline(line))

    if in_table:
        result.append(_render_table(table_lines))

    return "\n".join(result)


async def start(update: Update, _context):
    await update.message.reply_text(
        "Halo! 👋 Saya AI assistant untuk membantu kamu mencari data dan menganalisis informasi.\n\n"
        "Langsung tanya aja, misalnya:\n"
        "  • \"Stok produk X di semua gudang\"\n"
        "  • \"Total penjualan bulan ini\"\n"
        "  • \"Top 10 customer\"\n"
        "  • \"Produk paling laris\"\n\n"
        "Ada yang bisa saya bantu? 😊"
    )


def _is_admin(user_id: int) -> bool:
    return user_id in settings.authorized_users


async def handle_message(update: Update, context):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id if update.effective_user else 0
    message = update.message.text

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        ctx = chat_contexts.get(chat_id, [])
        result = await _agent.run(message, ctx)
        chat_contexts[chat_id] = result["context"]

        text = (result.get("response") or "").strip()
        if not text:
            text = "Maaf, tidak bisa memproses. Coba tanya dengan cara lain."

        if len(text) > MAX_TELEGRAM_MSG:
            text = text[: MAX_TELEGRAM_MSG - 100] + "\n\n... (pesan terpotong)"

        formatted = _format_telegram(text)
        try:
            await update.message.reply_text(formatted, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(text)

        sql_list = result.get("sql", [])
        if _is_admin(user_id) and sql_list:
            for sql in sql_list:
                try:
                    await update.message.reply_text(f"<pre>{sql}</pre>", parse_mode="HTML")
                except Exception:
                    await update.message.reply_text(sql)
    except Exception as e:
        logger.exception("Bot error")
        try:
            await update.message.reply_text(f"Error: {str(e)[:200]}")
        except Exception:
            pass


async def clear_context(update: Update, _context):
    chat_id = update.effective_chat.id
    chat_contexts.pop(chat_id, None)
    await update.message.reply_text("Riwayat percakapan dihapus.")


def build_bot() -> Application:
    app = (
        Application.builder()
        .token(settings.telegram_bot_token)
        .read_timeout(120)
        .write_timeout(120)
        .build()
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("clear", clear_context))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    return app


async def start_bot():
    global _bot_app
    if _bot_app:
        return
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN tidak diisi, bot tidak aktif")
        return
    _bot_app = build_bot()
    await _bot_app.initialize()
    await _bot_app.start()
    await _bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info("Bot started")


async def stop_bot():
    global _bot_app
    if _bot_app:
        await _bot_app.updater.stop()
        await _bot_app.stop()
        await _bot_app.shutdown()
        _bot_app = None
        logger.info("Bot stopped")
