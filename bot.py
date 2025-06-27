import os
import logging
import requests
import asyncio
from telegram import Update, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from io import BytesIO

BOT_TOKEN = os.getenv("BOT_TOKEN")
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        print("👋 Welcome to CreativeSync AI Bot!")

        "Use /ask <your question> to chat with Llama-3."
            
        "Use /news for trending news"

        "Use /image <prompt> to generate an image"

        "Use /help to see this again."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not TOGETHER_API_KEY:
        await update.message.reply_text("❌ TOGETHER_API_KEY not set.")
        return
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❗ Usage: /ask <your message>")
        return

    await update.message.chat.send_action(action="typing")
    headers = {
        "Authorization": f"Bearer {TOGETHER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "meta-llama/Llama-3-70b-instruct",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200
    }
    try:
        response = requests.post("https://api.together.xyz/v1/chat/completions", headers=headers, json=data)
        result = response.json()
        reply = result["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)
    except Exception as e:
        await update.message.reply_text("💥 Error contacting Llama-3 API.")

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not NEWS_API_KEY:
        await update.message.reply_text("❌ NEWS_API_KEY not set.")
        return

    await update.message.chat.send_action(action="typing")
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
        res = requests.get(url).json()
        articles = res.get("articles", [])[:5]
        reply = "📰 Top News:\n"
reply += "\n".join([f"{a.get('title', 'No Title')} - {a.get('url', 'No URL')}" for a in articles])
        await update.message.reply_text(reply)
    except Exception:
        await update.message.reply_text("💥 Error fetching news.")

async def image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not STABILITY_API_KEY:
        await update.message.reply_text("❌ STABILITY_API_KEY not set.")
        return
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❗ Usage: /image <description>")
        return

    await update.message.chat.send_action(action="upload_photo")
    try:
        stability_url = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"
        headers = {
            "Authorization": f"Bearer {STABILITY_API_KEY}",
            "Content-Type": "application/json"
        }
        json_data = {"text_prompts": [{"text": prompt}], "cfg_scale": 7, "height": 512, "width": 512, "samples": 1}
        res = requests.post(stability_url, headers=headers, json=json_data)
        image_data = res.content
        await update.message.reply_photo(photo=BytesIO(image_data))
    except Exception:
        await update.message.reply_text("💥 Error generating image.")

def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("news", news))
    app.add_handler(CommandHandler("image", image))
    app.run_polling()

if __name__ == "__main__":
    main()
