#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Bot de Telegram - Descargador de TikTok
# Autor: Aramis | Alojado en Railway

import os
import re
import uuid
import logging
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# ─── CONFIG ───────────────────────────────────────────────────────────────────
TOKEN = "7336405470:AAGtl5oh178FJReZsikUpKsfBiWugZu1YmU"
CARPETA_TEMP = "/tmp/"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── DESCARGADOR TIKTOK (via tikwm.com) ───────────────────────────────────────
def descargar_tiktok(url: str) -> str | None:
    try:
        api = requests.post(
            "https://www.tikwm.com/api/",
            data={"url": url, "hd": 1},
            headers={"User-Agent": "Mozilla/5.0"}
        ).json()

        if api.get("code") != 0:
            return None

        play_url = api["data"].get("hdplay") or api["data"].get("play")
        if not play_url:
            return None

        video = requests.get(play_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        ruta = CARPETA_TEMP + str(uuid.uuid4()) + ".mp4"
        with open(ruta, "wb") as f:
            f.write(video.content)
        return ruta

    except Exception as e:
        logger.error(f"Error descargando TikTok: {e}")
        return None

# ─── HANDLERS ─────────────────────────────────────────────────────────────────
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 *Bot Descargador de TikTok*\n\n"
        "Mándame cualquier link de TikTok y te envío el video sin marca de agua.\n\n"
        "Ejemplo:\n`https://vm.tiktok.com/xxxxx`",
        parse_mode="Markdown"
    )

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Cómo usarlo:*\n\n"
        "1. Copia el link de cualquier video de TikTok\n"
        "2. Pégalo aquí en el chat\n"
        "3. Espera unos segundos y recibes el video ✅\n\n"
        "Funciona con links cortos `vm.tiktok.com` y largos `tiktok.com/@user/video/...`",
        parse_mode="Markdown"
    )

async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()

    if not re.search(r'tiktok\.com|vm\.tiktok\.com', texto):
        await update.message.reply_text(
            "❌ Eso no parece un link de TikTok.\n"
            "Envíame un link como: `https://vm.tiktok.com/xxxxx`",
            parse_mode="Markdown"
        )
        return

    msg = await update.message.reply_text("⏳ Descargando video, espera...")

    ruta = descargar_tiktok(texto)

    if ruta and os.path.exists(ruta):
        await msg.edit_text("📤 Enviando video...")
        try:
            with open(ruta, 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption="✅ Descargado sin marca de agua 🎵",
                    supports_streaming=True
                )
            await msg.delete()
        except Exception as e:
            logger.error(f"Error enviando video: {e}")
            await msg.edit_text("❌ El video es muy grande (límite Telegram: 50MB).")
        finally:
            if os.path.exists(ruta):
                os.remove(ruta)
    else:
        await msg.edit_text(
            "❌ No pude descargar ese video.\n\n"
            "Posibles causas:\n"
            "• El video es privado\n"
            "• El link expiró\n"
            "• Intenta de nuevo en unos segundos"
        )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("🤖 Bot iniciado y escuchando...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    
