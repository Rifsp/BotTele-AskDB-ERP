import logging
import re

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import settings
from app.agents import route_message

logger = logging.getLogger(__name__)

chat_contexts: dict[int, list[dict]] = {}
_bot_app: Application | None = None

MAX_TELEGRAM_MSG = 4000


def _is_authorized(user_id: int) -> bool:
    allowed = settings.authorized_users
    if not allowed:
        return True
    return user_id in allowed


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


async def _check_auth(update: Update) -> bool:
    uid = update.effective_user.id if update.effective_user else 0
    if not _is_authorized(uid):
        logger.warning("Unauthorized access from user_id=%d", uid)
        await update.message.reply_text("Maaf, Anda tidak memiliki akses ke bot ini.")
        return False
    return True


async def start(update: Update, _context):
    if not await _check_auth(update):
        return
    await update.message.reply_text(
        "Halo! Saya asisten database Anda. Saya bisa membantu:\n\n"
        "• Menjawab pertanyaan tentang data\n"
        "• Menganalisis struktur database\n"
        "• Mendeteksi anomali data\n"
        "• Membuat laporan\n\n"
        "Silakan tanyakan sesuatu!"
    )


async def handle_message(update: Update, context):
    if not await _check_auth(update):
        return
    chat_id = update.effective_chat.id
    message = update.message.text

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        ctx = chat_contexts.get(chat_id, [])
        result = await route_message(message, ctx)
        chat_contexts[chat_id] = result["context"]

        text = (result.get("response") or "").strip()
        if not text:
            logger.warning("Empty response from agent; messages=%d, context=%d", len(ctx), len(result.get("context", [])))
            text = "Maaf, saya tidak bisa memproses pertanyaan itu. Coba tanya dengan cara lain."

        if len(text) > MAX_TELEGRAM_MSG:
            text = text[: MAX_TELEGRAM_MSG - 100] + "\n\n... (pesan terpotong, ajukan pertanyaan lebih spesifik)"

        formatted = _format_telegram(text)
        try:
            await update.message.reply_text(formatted, parse_mode="HTML")
        except Exception:
            await update.message.reply_text(text)

    except Exception as e:
        logger.exception("Bot error")
        try:
            await update.message.reply_text(f"Error: {str(e)[:200]}")
        except Exception:
            pass


async def clear_context(update: Update, _context):
    if not await _check_auth(update):
        return
    chat_id = update.effective_chat.id
    chat_contexts.pop(chat_id, None)
    await update.message.reply_text("Riwayat percakapan dihapus. Mulai dari awal.")


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
    await _bot_app.updater.start_polling()
    logger.info("Telegram bot started")


async def stop_bot():
    global _bot_app
    if _bot_app:
        await _bot_app.updater.stop()
        await _bot_app.stop()
        await _bot_app.shutdown()
        _bot_app = None
        logger.info("Telegram bot stopped")
