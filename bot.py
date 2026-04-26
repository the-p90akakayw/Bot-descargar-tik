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
TOKEN = os.environ.get("7336405470:AAGtl5oh178FJReZsikUpKsfBiWugZu1YmU")  # Se pone en Railway como variable de entorno
CARPETA_TEMP = "/tmp/"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── DESCARGADOR TIKTOK ───────────────────────────────────────────────────────
COOKIES = {
    'perf_feed_cache': '{%22expireTimestamp%22:1718632800000%2C%22itemIds%22:[%227379653241388240161%22%2C%227374213452182719749%22%2C%227352243264180849925%22]}',
    'tt_chain_token': 'zcCEGW55CjWsgf6gIV9gHA==',
    'msToken': '1a8hsWMj2hqo1X5XeCKqspQzbH6PiG3hLfvUHP1vxK95mxrVhjOOxX53L4mCiJIdgj7EQ7u4MYNl5tlKBiizyUOVG6NMYZX8n_6XzTpLkkvHnMgSxR6fTXdWjchKLWTxGrwMPmHgSTrRDeZXknAKnES8',
    'tt_csrf_token': 'F4h33dkH-Wee1KfLOU-0sLLke14J7ze5j5Lw',
    'tiktok_webapp_theme': 'light',
    's_v_web_id': 'verify_lxg8mwuv_1o3cv7zC_79mq_4UW7_8cg0_MIzj78s0HFfN',
}

HEADERS = {
    'accept': '*/*',
    'accept-language': 'id,en;q=0.9',
    'user-agent': 'Mozilla/5.0 (Linux; Android 12; Pixel 6 Build/SQ3A.220705.004; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/125.0.0.0 Mobile Safari/537.36',
}

def descargar_tiktok(url: str) -> str | None:
    """Descarga un video de TikTok y devuelve la ruta del archivo."""
    try:
        with requests.Session() as s:
            # Resolver URL corta si es necesario
            if 'video' not in url:
                resp = s.get(url, cookies=COOKIES, headers=HEADERS).text
                video_id = re.search('"share_item_id":"(\d+)"', resp).group(1)
            else:
                video_id = re.search('video/(\d+)', url).group(1)

            # Obtener URL directa del video
            api_url = (
                f'https://www.tiktok.com/api/item/detail/'
                f'?aid=1988&app_id=1180&itemId={video_id}&item_id={video_id}'
                f'&device_platform=web_mobile&language=id-ID'
            )
            play_url = s.get(api_url, cookies=COOKIES, headers=HEADERS).json()
            play_url = play_url['itemInfo']['itemStruct']['video']['playAddr']

            # Descargar el video
            video = requests.get(play_url, headers=HEADERS, cookies=COOKIES)
            ruta = CARPETA_TEMP + str(uuid.uuid4()) + ".mp4"
            with open(ruta, 'wb') as f:
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

    # Verificar si es un link de TikTok
    if not re.search(r'tiktok\.com|vm\.tiktok\.com', texto):
        await update.message.reply_text(
            "❌ Eso no parece un link de TikTok.\n"
            "Envíame un link como: `https://vm.tiktok.com/xxxxx`",
            parse_mode="Markdown"
        )
        return

    # Enviar mensaje de espera
    msg = await update.message.reply_text("⏳ Descargando video, espera...")

    # Descargar
    ruta = descargar_tiktok(texto)

    if ruta and os.path.exists(ruta):
        await msg.edit_text("📤 Enviando video...")
        try:
            with open(ruta, 'rb') as video:
                await update.message.reply_video(
                    video=video,
                    caption="✅ Descargado sin marca de agua\n🤖 @TuBotAqui",
                    supports_streaming=True
                )
            await msg.delete()
        except Exception as e:
            logger.error(f"Error enviando video: {e}")
            await msg.edit_text("❌ El video es muy grande para enviarlo por Telegram (límite 50MB).")
        finally:
            # Borrar archivo temporal
            if os.path.exists(ruta):
                os.remove(ruta)
    else:
        await msg.edit_text(
            "❌ No pude descargar ese video.\n\n"
            "Posibles causas:\n"
            "• El video es privado\n"
            "• El link expiró\n"
            "• TikTok bloqueó la descarga temporalmente"
        )

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    if not TOKEN:
        raise ValueError("❌ Falta la variable de entorno BOT_TOKEN")

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("🤖 Bot iniciado y escuchando...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
          
