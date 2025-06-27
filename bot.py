#!/usr/bin/env python3
"""
Telegram Bot for Crypto Enthusiasts, Gamers & Students
Smart assistant with AI chat, crypto prices, news, and image generation
"""

import os
import logging
import asyncio
import json
from datetime import datetime
from typing import Optional

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
TOGETHER_API_KEY = os.getenv('TOGETHER_API_KEY')
NEWS_API_KEY = os.getenv('NEWS_API_KEY')
IMAGE_API_KEY = os.getenv('IMAGE_API_KEY')

try:
    import aiohttp
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import (
        Application, 
        CommandHandler, 
        MessageHandler, 
        filters, 
        ContextTypes
    )
    TELEGRAM_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Telegram imports failed: {e}")
    print("This is normal in development. The bot will work when deployed with proper dependencies.")
    TELEGRAM_AVAILABLE = False

# API URLs
TOGETHER_API_URL = "https://api.together.xyz/v1/chat/completions"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
NEWS_API_URL = "https://newsapi.org/v2/everything"
IMAGE_API_URL = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"

class TelegramBot:
    def __init__(self):
        self.session = None
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        welcome_text = f"""
🚀 Hey {user.first_name}! Welcome to your smart crypto & gaming buddy! 

I'm here to help you with:
💬 AI Chat - Ask me anything about crypto, gaming, or studies
💰 Crypto Prices - Get live market data
📰 Latest News - Crypto and gaming headlines
🎨 Image Generation - Create awesome images
📞 Contact Info - Reach my creator

Ready to dive in? Try /ask followed by your question!

Examples:
• /ask What's the best strategy for DeFi?
• /price bitcoin
• /news
• /image futuristic gaming setup
"""
        
        keyboard = [
            [InlineKeyboardButton("💰 Crypto Prices", callback_data='prices')],
            [InlineKeyboardButton("📰 Latest News", callback_data='news')],
            [InlineKeyboardButton("🎨 Generate Image", callback_data='image')],
            [InlineKeyboardButton("📞 Contact", callback_data='contact')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(welcome_text, reply_markup=reply_markup)

    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /ask command with AI chat"""
        if not context.args:
            await update.message.reply_text(
                "🤔 What's on your mind? Use: /ask <your question>\n\n"
                "Examples:\n"
                "• /ask Explain blockchain in simple terms\n"
                "• /ask Best gaming laptops under $1000\n"
                "• /ask Help me with calculus derivatives"
            )
            return
        
        question = " ".join(context.args)
        
        # Send typing indicator
        await update.message.reply_chat_action("typing")
        
        try:
            response = await self.get_ai_response(question)
            
            # Split long responses if needed
            if len(response) > 4096:
                for i in range(0, len(response), 4096):
                    await update.message.reply_text(response[i:i+4096])
            else:
                await update.message.reply_text(response)
                
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            await update.message.reply_text(
                "🤖 Oops! My AI brain is taking a quick break. Try again in a moment!"
            )

    async def price_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /price command for crypto prices"""
        if not context.args:
            await update.message.reply_text(
                "💰 Which crypto are you curious about?\n\n"
                "Usage: /price <symbol>\n"
                "Examples: /price bitcoin, /price ethereum, /price dogecoin"
            )
            return
        
        symbol = context.args[0].lower()
        
        await update.message.reply_chat_action("typing")
        
        try:
            price_data = await self.get_crypto_price(symbol)
            if price_data:
                await update.message.reply_text(price_data)
            else:
                await update.message.reply_text(
                    f"❌ Couldn't find price data for '{symbol}'. "
                    "Try using the full name or check the spelling!"
                )
        except Exception as e:
            logger.error(f"Price fetch error: {e}")
            await update.message.reply_text(
                "💸 Price servers are busy right now. Try again in a moment!"
            )

    async def news_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /news command for latest news"""
        await update.message.reply_chat_action("typing")
        
        try:
            news_data = await self.get_latest_news()
            if news_data:
                await update.message.reply_text(news_data, parse_mode='HTML', disable_web_page_preview=True)
            else:
                await update.message.reply_text("📰 No fresh news right now. Check back soon!")
        except Exception as e:
            logger.error(f"News fetch error: {e}")
            await update.message.reply_text(
                "📡 News servers are updating. Try again in a moment!"
            )

    async def image_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /image command for image generation"""
        if not context.args:
            await update.message.reply_text(
                "🎨 What should I create for you?\n\n"
                "Usage: /image <description>\n"
                "Examples:\n"
                "• /image cyberpunk gaming setup\n"
                "• /image cute crypto mascot\n"
                "• /image futuristic city at sunset"
            )
            return
        
        prompt = " ".join(context.args)
        
        await update.message.reply_chat_action("upload_photo")
        
        try:
            await update.message.reply_text(
                f"🎨 Image generation requested: {prompt}\n"
                "Note: Image generation requires Stability.ai API key configuration."
            )
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            await update.message.reply_text(
                "🖼️ Image generation is temporarily offline. Try again later!"
            )

    async def contact_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /contact command"""
        contact_info = """
📞 **Contact Information**

💌 **Email:** your.email@example.com
📱 **WhatsApp:** +1234567890

🚀 **About this bot:**
Built with love for the crypto & gaming community!
Powered by AI and real-time data feeds.

💡 **Feedback & Suggestions:**
Feel free to reach out with ideas or bug reports!
"""
        await update.message.reply_text(contact_info, parse_mode='Markdown')

    async def get_ai_response(self, question: str) -> str:
        """Get AI response from Together.ai"""
        if not TOGETHER_API_KEY:
            return "🤖 AI chat needs configuration. Please contact the admin to set TOGETHER_API_KEY!"
        
        headers = {
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "meta-llama/Llama-3-70b-chat-hf",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful assistant for crypto enthusiasts, gamers, and students. Be friendly, knowledgeable, and concise. Use emojis appropriately and speak like a knowledgeable friend."
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(TOGETHER_API_URL, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    raise Exception(f"API returned status {response.status}")

    async def get_crypto_price(self, symbol: str) -> Optional[str]:
        """Get crypto price from CoinGecko"""
        url = f"{COINGECKO_API_URL}/simple/price"
        params = {
            "ids": symbol,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    if symbol in data:
                        coin_data = data[symbol]
                        price = coin_data.get("usd", "N/A")
                        change_24h = coin_data.get("usd_24h_change", 0)
                        market_cap = coin_data.get("usd_market_cap", "N/A")
                        
                        change_emoji = "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️"
                        change_color = "+" if change_24h > 0 else ""
                        
                        return f"""
💰 **{symbol.upper()} Price Update**

💵 **Price:** ${price:,.2f} USD
{change_emoji} **24h Change:** {change_color}{change_24h:.2f}%
📊 **Market Cap:** ${market_cap:,.0f} USD

🕒 **Updated:** {datetime.now().strftime("%H:%M UTC")}
"""
                return None

    async def get_latest_news(self) -> Optional[str]:
        """Get latest crypto and gaming news"""
        if not NEWS_API_KEY:
            return "📰 News service needs configuration. Please contact the admin to set NEWS_API_KEY!"
        
        headers = {"X-API-Key": NEWS_API_KEY}
        params = {
            "q": "crypto OR bitcoin OR gaming OR esports",
            "sortBy": "publishedAt",
            "pageSize": 3,
            "language": "en"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(NEWS_API_URL, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    articles = data.get("articles", [])
                    
                    if not articles:
                        return "📰 No fresh news available right now!"
                    
                    news_text = "📰 **Latest Headlines:**\n\n"
                    
                    for i, article in enumerate(articles[:3], 1):
                        title = article.get("title", "No title")
                        source = article.get("source", {}).get("name", "Unknown")
                        url = article.get("url", "")
                        
                        news_text += f"**{i}. {title}**\n"
                        news_text += f"🔗 Source: {source}\n"
                        if url:
                            news_text += f"📖 <a href='{url}'>Read more</a>\n\n"
                    
                    return news_text
                return None

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        message_text = update.message.text.lower()
        
        if any(keyword in message_text for keyword in ["hi", "hello", "hey", "start"]):
            await update.message.reply_text(
                "👋 Hey there! I'm your crypto & gaming buddy. "
                "Try /ask followed by your question, or use /start to see all commands!"
            )
        else:
            await update.message.reply_text(
                "🤔 Not sure what you mean. Try:\n"
                "• /ask <question> - Chat with AI\n"
                "• /price <crypto> - Get prices\n"
                "• /news - Latest headlines\n"
                "• /image <description> - Generate images"
            )

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle errors"""
        logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot"""
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN environment variable is required!")
        print("Get your bot token from @BotFather on Telegram")
        return
    
    if not TELEGRAM_AVAILABLE:
        print("❌ Telegram bot library not available in development environment")
        print("This is normal - the bot will work when deployed with proper dependencies")
        return
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    bot_instance = TelegramBot()
    
    # Add handlers
    app.add_handler(CommandHandler("start", bot_instance.start_command))
    app.add_handler(CommandHandler("ask", bot_instance.ask_command))
    app.add_handler(CommandHandler("price", bot_instance.price_command))
    app.add_handler(CommandHandler("news", bot_instance.news_command))
    app.add_handler(CommandHandler("image", bot_instance.image_command))
    app.add_handler(CommandHandler("contact", bot_instance.contact_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot_instance.handle_message))
    
    # Add error handler
    app.add_error_handler(bot_instance.error_handler)
    
    print("🚀 Bot starting...")
    print("🔑 Make sure to set your environment variables:")
    print("   - BOT_TOKEN (required)")
    print("   - TOGETHER_API_KEY (for AI chat)")
    print("   - NEWS_API_KEY (for news)")
    print("   - IMAGE_API_KEY (for image generation)")
    
    # Start the bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()