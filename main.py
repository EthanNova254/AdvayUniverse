#!/usr/bin/env python3
"""
Advay Universe Telegram Bot
A feature-rich Telegram bot with AI, entertainment, utilities, and more!
"""

import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
import random
import json
import urllib.parse

import requests
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode, ChatAction
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
WAITING_FOR_PROMPT, WAITING_FOR_LOCATION, WAITING_FOR_CURRENCY, WAITING_FOR_QR = range(4)

class AdvayUniverseBot:
    """Main bot class with all features"""
    
    def __init__(self, token: str, admin_id: str):
        self.token = token
        self.admin_id = int(admin_id) if admin_id else None
        
        # In-memory storage
        self.users: Dict[int, dict] = {}
        self.user_activity: Dict[int, int] = {}
        self.group_settings: Dict[int, dict] = {}
        self.bot_stats = {
            'total_commands': 0,
            'start_time': datetime.now(),
            'features_used': {}
        }
    
    def get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Create main menu keyboard"""
        keyboard = [
            [KeyboardButton("🤖 AI Features"), KeyboardButton("🎉 Entertainment")],
            [KeyboardButton("💰 Utilities"), KeyboardButton("📊 Crypto & Finance")],
            [KeyboardButton("🌐 Group Tools"), KeyboardButton("⚙️ Admin Panel")],
            [KeyboardButton("ℹ️ Help")]
        ]
        return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    def get_ai_keyboard(self) -> InlineKeyboardMarkup:
        """AI features menu"""
        keyboard = [
            [InlineKeyboardButton("🎨 Generate Image", callback_data="ai_image")],
            [InlineKeyboardButton("💬 AI Chat", callback_data="ai_chat")],
            [InlineKeyboardButton("✍️ Story Generator", callback_data="ai_story")],
            [InlineKeyboardButton("🎭 Creative Writing", callback_data="ai_creative")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_entertainment_keyboard(self) -> InlineKeyboardMarkup:
        """Entertainment features menu"""
        keyboard = [
            [InlineKeyboardButton("😂 Random Meme", callback_data="ent_meme")],
            [InlineKeyboardButton("🎭 Random Joke", callback_data="ent_joke")],
            [InlineKeyboardButton("💭 Inspirational Quote", callback_data="ent_quote")],
            [InlineKeyboardButton("🐕 Random Dog", callback_data="ent_dog")],
            [InlineKeyboardButton("🐱 Random Cat", callback_data="ent_cat")],
            [InlineKeyboardButton("🍕 Random Recipe", callback_data="ent_recipe")],
            [InlineKeyboardButton("🎲 Random Activity", callback_data="ent_activity")],
            [InlineKeyboardButton("🤓 Random Fact", callback_data="ent_fact")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_utilities_keyboard(self) -> InlineKeyboardMarkup:
        """Utilities features menu"""
        keyboard = [
            [InlineKeyboardButton("🌤️ Weather", callback_data="util_weather")],
            [InlineKeyboardButton("💱 Currency Converter", callback_data="util_currency")],
            [InlineKeyboardButton("📱 QR Code Generator", callback_data="util_qr")],
            [InlineKeyboardButton("📚 Book Search", callback_data="util_book")],
            [InlineKeyboardButton("🌍 Country Info", callback_data="util_country")],
            [InlineKeyboardButton("🕐 World Time", callback_data="util_time")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    def get_crypto_keyboard(self) -> InlineKeyboardMarkup:
        """Crypto & Finance menu"""
        keyboard = [
            [InlineKeyboardButton("₿ Bitcoin Price", callback_data="crypto_btc")],
            [InlineKeyboardButton("Ξ Ethereum Price", callback_data="crypto_eth")],
            [InlineKeyboardButton("Ð Dogecoin Price", callback_data="crypto_doge")],
            [InlineKeyboardButton("📊 Top 10 Cryptos", callback_data="crypto_top10")],
            [InlineKeyboardButton("💹 Market Overview", callback_data="crypto_market")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")]
        ]
        return InlineKeyboardMarkup(keyboard)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat = update.effective_chat
        
        # Track user
        if user.id not in self.users:
            self.users[user.id] = {
                'username': user.username,
                'first_seen': datetime.now(),
                'last_active': datetime.now()
            }
        
        self.user_activity[user.id] = self.user_activity.get(user.id, 0) + 1
        
        # Group welcome
        if chat.type in ['group', 'supergroup']:
            welcome_msg = (
                f"👋 Hello everyone! I'm *Advay Universe Bot*\n\n"
                f"I can help with:\n"
                f"🤖 AI Image & Text Generation\n"
                f"🎉 Entertainment (Memes, Jokes, etc.)\n"
                f"💰 Utilities (Weather, Currency, etc.)\n"
                f"📊 Crypto Prices & Market Data\n\n"
                f"Use /help to see all commands!"
            )
            await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
            return
        
        # Private chat welcome
        welcome_msg = (
            f"🌟 *Welcome to Advay Universe, {user.first_name}!* 🌟\n\n"
            f"I'm your all-in-one bot with amazing features:\n\n"
            f"🤖 *AI Features* - Generate images, chat with AI\n"
            f"🎉 *Entertainment* - Memes, jokes, quotes, animals\n"
            f"💰 *Utilities* - Weather, currency, QR codes\n"
            f"📊 *Crypto* - Real-time cryptocurrency prices\n"
            f"🌐 *Group Tools* - Auto-welcome, management\n\n"
            f"👇 *Choose from the menu below or use /help*"
        )
        
        await update.message.reply_text(
            welcome_msg,
            reply_markup=self.get_main_keyboard(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📖 *Advay Universe Bot - Help Guide*\n\n"
            "*🤖 AI Commands:*\n"
            "/imagine <prompt> - Generate AI image\n"
            "/ask <question> - Ask AI anything\n"
            "/story <topic> - Generate a story\n\n"
            "*🎉 Entertainment Commands:*\n"
            "/meme - Random meme\n"
            "/joke - Random joke\n"
            "/quote - Inspirational quote\n"
            "/dog - Random dog image\n"
            "/cat - Random cat image\n"
            "/recipe - Random recipe\n"
            "/activity - Suggest an activity\n\n"
            "*💰 Utility Commands:*\n"
            "/weather <city> - Get weather\n"
            "/convert <amount> <from> <to> - Currency\n"
            "/qr <text> - Generate QR code\n"
            "/book <title> - Search books\n"
            "/country <name> - Country info\n\n"
            "*📊 Crypto Commands:*\n"
            "/btc - Bitcoin price\n"
            "/eth - Ethereum price\n"
            "/doge - Dogecoin price\n"
            "/crypto <symbol> - Any crypto price\n\n"
            "*⚙️ Admin Commands:*\n"
            "/broadcast <message> - Send to all users\n"
            "/stats - Bot statistics\n\n"
            "💡 *Tip: Use the menu buttons for easy navigation!*"
        )
        
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)
    
    async def handle_menu_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle main menu button presses"""
        text = update.message.text
        
        if text == "🤖 AI Features":
            await update.message.reply_text(
                "🤖 *AI Features*\n\nChoose an AI feature below:",
                reply_markup=self.get_ai_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif text == "🎉 Entertainment":
            await update.message.reply_text(
                "🎉 *Entertainment Hub*\n\nPick your entertainment:",
                reply_markup=self.get_entertainment_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif text == "💰 Utilities":
            await update.message.reply_text(
                "💰 *Utilities*\n\nSelect a utility tool:",
                reply_markup=self.get_utilities_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif text == "📊 Crypto & Finance":
            await update.message.reply_text(
                "📊 *Crypto & Finance*\n\nCheck cryptocurrency prices:",
                reply_markup=self.get_crypto_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif text == "🌐 Group Tools":
            group_text = (
                "🌐 *Group Tools*\n\n"
                "Add me to your group for:\n"
                "• Auto-welcome new members\n"
                "• Group statistics\n"
                "• Fun group interactions\n\n"
                "Just add me and I'll work automatically!"
            )
            await update.message.reply_text(group_text, parse_mode=ParseMode.MARKDOWN)
        
        elif text == "⚙️ Admin Panel":
            if update.effective_user.id == self.admin_id:
                admin_text = (
                    "⚙️ *Admin Panel*\n\n"
                    "Available commands:\n"
                    "/broadcast <message> - Send to all users\n"
                    "/stats - View bot statistics\n"
                    "/users - List all users\n"
                    "/export - Export user data"
                )
                await update.message.reply_text(admin_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("❌ Admin access required!")
        
        elif text == "ℹ️ Help":
            await self.help_command(update, context)
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        self.bot_stats['total_commands'] += 1
        self.bot_stats['features_used'][data] = self.bot_stats['features_used'].get(data, 0) + 1
        
        # AI Features
        if data == "ai_image":
            await query.edit_message_text(
                "🎨 *AI Image Generator*\n\n"
                "Send me a description and I'll create an image!\n\n"
                "Example: _A futuristic city at sunset_",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PROMPT
        
        elif data == "ai_chat":
            await query.edit_message_text(
                "💬 *AI Chat*\n\n"
                "Ask me anything! I'll use AI to respond.\n\n"
                "Example: _Explain quantum computing_",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PROMPT
        
        elif data == "ai_story":
            await query.edit_message_text(
                "✍️ *Story Generator*\n\n"
                "Give me a topic and I'll write a story!\n\n"
                "Example: _A robot learning to love_",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PROMPT
        
        elif data == "ai_creative":
            await query.edit_message_text(
                "🎭 *Creative Writing*\n\n"
                "Tell me what to write about!\n\n"
                "Example: _A poem about the ocean_",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_PROMPT
        
        # Entertainment
        elif data == "ent_meme":
            await self.send_meme(query)
        
        elif data == "ent_joke":
            await self.send_joke(query)
        
        elif data == "ent_quote":
            await self.send_quote(query)
        
        elif data == "ent_dog":
            await self.send_dog(query)
        
        elif data == "ent_cat":
            await self.send_cat(query)
        
        elif data == "ent_recipe":
            await self.send_recipe(query)
        
        elif data == "ent_activity":
            await self.send_activity(query)
        
        elif data == "ent_fact":
            await self.send_fact(query)
        
        # Crypto
        elif data.startswith("crypto_"):
            await self.handle_crypto(query, data)
        
        # Utilities
        elif data == "util_weather":
            await query.edit_message_text(
                "🌤️ *Weather Information*\n\n"
                "Send me a city name!\n\n"
                "Example: _London_",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_LOCATION
        
        elif data == "util_currency":
            await query.edit_message_text(
                "💱 *Currency Converter*\n\n"
                "Format: amount from to\n\n"
                "Example: _100 USD EUR_",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_CURRENCY
        
        elif data == "util_qr":
            await query.edit_message_text(
                "📱 *QR Code Generator*\n\n"
                "Send me text or URL to convert!\n\n"
                "Example: _https://telegram.org_",
                parse_mode=ParseMode.MARKDOWN
            )
            return WAITING_FOR_QR
        
        elif data == "util_book":
            await query.edit_message_text(
                "📚 *Book Search*\n\n"
                "Send me a book title!\n\n"
                "Example: _1984_",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "util_country":
            await query.edit_message_text(
                "🌍 *Country Information*\n\n"
                "Send me a country name!\n\n"
                "Example: _Japan_",
                parse_mode=ParseMode.MARKDOWN
            )
        
        elif data == "main_menu":
            await query.message.reply_text(
                "🏠 *Main Menu*\n\nChoose a category:",
                reply_markup=self.get_main_keyboard(),
                parse_mode=ParseMode.MARKDOWN
            )
    
    async def send_meme(self, query):
        """Fetch and send a random meme"""
        await query.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
        
        try:
            # Try meme-api.com first
            response = requests.get("https://meme-api.com/gimme", timeout=10)
            if response.status_code == 200:
                data = response.json()
                await query.message.reply_photo(
                    photo=data['url'],
                    caption=f"😂 *{data['title']}*\n\n👍 {data.get('ups', 0)} upvotes\nr/{data.get('subreddit', 'memes')}",
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        except Exception as e:
            logger.error(f"Meme API error: {e}")
        
        await query.message.reply_text("😅 Couldn't fetch a meme right now. Try again!")
    
    async def send_joke(self, query):
        """Fetch and send a random joke"""
        try:
            # Try icanhazdadjoke.com
            headers = {'Accept': 'application/json'}
            response = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=10)
            
            if response.status_code == 200:
                joke = response.json()['joke']
                await query.message.reply_text(f"🎭 *Dad Joke*\n\n{joke}", parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Joke API error: {e}")
        
        # Fallback jokes
        fallback_jokes = [
            "Why don't scientists trust atoms? Because they make up everything!",
            "Why did the scarecrow win an award? He was outstanding in his field!",
            "What do you call a bear with no teeth? A gummy bear!",
        ]
        await query.message.reply_text(f"🎭 *Joke*\n\n{random.choice(fallback_jokes)}", parse_mode=ParseMode.MARKDOWN)
    
    async def send_quote(self, query):
        """Fetch and send an inspirational quote"""
        try:
            response = requests.get("https://api.quotable.io/random", timeout=10)
            if response.status_code == 200:
                data = response.json()
                quote_text = f"💭 *Quote of the Moment*\n\n_{data['content']}_\n\n— *{data['author']}*"
                await query.message.reply_text(quote_text, parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Quote API error: {e}")
        
        await query.message.reply_text("💭 Couldn't fetch a quote right now. Try again!")
    
    async def send_dog(self, query):
        """Send random dog image"""
        await query.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
        
        try:
            response = requests.get("https://dog.ceo/api/breeds/image/random", timeout=10)
            if response.status_code == 200:
                data = response.json()
                await query.message.reply_photo(
                    photo=data['message'],
                    caption="🐕 Here's a random good boy/girl!"
                )
                return
        except Exception as e:
            logger.error(f"Dog API error: {e}")
        
        await query.message.reply_text("🐕 Couldn't fetch a dog image. Try again!")
    
    async def send_cat(self, query):
        """Send random cat image"""
        await query.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
        
        try:
            response = requests.get("https://api.thecatapi.com/v1/images/search", timeout=10)
            if response.status_code == 200:
                data = response.json()
                await query.message.reply_photo(
                    photo=data[0]['url'],
                    caption="🐱 Here's a random feline friend!"
                )
                return
        except Exception as e:
            logger.error(f"Cat API error: {e}")
        
        await query.message.reply_text("🐱 Couldn't fetch a cat image. Try again!")
    
    async def send_recipe(self, query):
        """Send random recipe"""
        try:
            response = requests.get("https://www.themealdb.com/api/json/v1/1/random.php", timeout=10)
            if response.status_code == 200:
                meal = response.json()['meals'][0]
                
                # Build ingredients list
                ingredients = []
                for i in range(1, 21):
                    ingredient = meal.get(f'strIngredient{i}')
                    measure = meal.get(f'strMeasure{i}')
                    if ingredient and ingredient.strip():
                        ingredients.append(f"• {measure} {ingredient}".strip())
                
                recipe_text = (
                    f"🍕 *{meal['strMeal']}*\n\n"
                    f"📍 Category: {meal['strCategory']}\n"
                    f"🌍 Cuisine: {meal['strArea']}\n\n"
                    f"*Ingredients:*\n" + "\n".join(ingredients[:10]) + "\n\n"
                    f"🔗 [Full Recipe]({meal['strSource'] or meal['strYoutube']})"
                )
                
                await query.message.reply_photo(
                    photo=meal['strMealThumb'],
                    caption=recipe_text,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
        except Exception as e:
            logger.error(f"Recipe API error: {e}")
        
        await query.message.reply_text("🍕 Couldn't fetch a recipe. Try again!")
    
    async def send_activity(self, query):
        """Suggest random activity"""
        try:
            response = requests.get("https://www.boredapi.com/api/activity", timeout=10)
            if response.status_code == 200:
                activity = response.json()
                activity_text = (
                    f"🎲 *Activity Suggestion*\n\n"
                    f"*{activity['activity']}*\n\n"
                    f"Type: {activity['type'].capitalize()}\n"
                    f"Participants: {activity['participants']}\n"
                    f"Price: {'$' * int(activity['price'] * 5) if activity['price'] > 0 else 'Free'}\n"
                )
                await query.message.reply_text(activity_text, parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Activity API error: {e}")
        
        await query.message.reply_text("🎲 Couldn't fetch an activity. Try again!")
    
    async def send_fact(self, query):
        """Send random fact"""
        try:
            num = random.randint(1, 1000)
            response = requests.get(f"http://numbersapi.com/{num}/trivia", timeout=10)
            if response.status_code == 200:
                fact = response.text
                await query.message.reply_text(f"🤓 *Random Fact*\n\n{fact}", parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Fact API error: {e}")
        
        await query.message.reply_text("🤓 Couldn't fetch a fact. Try again!")
    
    async def handle_crypto(self, query, data):
        """Handle cryptocurrency queries"""
        try:
            if data == "crypto_btc":
                crypto_id = "bitcoin"
                symbol = "₿"
            elif data == "crypto_eth":
                crypto_id = "ethereum"
                symbol = "Ξ"
            elif data == "crypto_doge":
                crypto_id = "dogecoin"
                symbol = "Ð"
            elif data == "crypto_top10":
                await self.send_top_cryptos(query)
                return
            elif data == "crypto_market":
                await self.send_market_overview(query)
                return
            else:
                return
            
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd,eur,gbp&include_24hr_change=true&include_market_cap=true"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()[crypto_id]
                
                change_emoji = "📈" if data.get('usd_24h_change', 0) > 0 else "📉"
                change_color = "+" if data.get('usd_24h_change', 0) > 0 else ""
                
                crypto_text = (
                    f"{symbol} *{crypto_id.upper()}*\n\n"
                    f"💵 USD: ${data['usd']:,.2f}\n"
                    f"💶 EUR: €{data['eur']:,.2f}\n"
                    f"💷 GBP: £{data['gbp']:,.2f}\n\n"
                    f"{change_emoji} 24h Change: {change_color}{data.get('usd_24h_change', 0):.2f}%\n"
                    f"📊 Market Cap: ${data.get('usd_market_cap', 0):,.0f}"
                )
                
                await query.message.reply_text(crypto_text, parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Crypto API error: {e}")
        
        await query.message.reply_text("📊 Couldn't fetch crypto data. Try again!")
    
    async def send_top_cryptos(self, query):
        """Send top 10 cryptocurrencies"""
        try:
            url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                cryptos = response.json()
                
                crypto_list = "📊 *Top 10 Cryptocurrencies*\n\n"
                
                for i, crypto in enumerate(cryptos, 1):
                    change_emoji = "📈" if crypto['price_change_percentage_24h'] > 0 else "📉"
                    crypto_list += (
                        f"{i}. *{crypto['symbol'].upper()}* - ${crypto['current_price']:,.2f}\n"
                        f"   {change_emoji} {crypto['price_change_percentage_24h']:.2f}%\n\n"
                    )
                
                await query.message.reply_text(crypto_list, parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Top cryptos error: {e}")
        
        await query.message.reply_text("📊 Couldn't fetch top cryptos. Try again!")
    
    async def send_market_overview(self, query):
        """Send market overview"""
        try:
            url = "https://api.coingecko.com/api/v3/global"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()['data']
                
                market_text = (
                    f"💹 *Crypto Market Overview*\n\n"
                    f"🌐 Total Market Cap: ${data['total_market_cap']['usd']:,.0f}\n"
                    f"📊 24h Volume: ${data['total_volume']['usd']:,.0f}\n"
                    f"₿ BTC Dominance: {data['market_cap_percentage']['btc']:.2f}%\n"
                    f"Ξ ETH Dominance: {data['market_cap_percentage']['eth']:.2f}%\n"
                    f"🪙 Active Cryptos: {data['active_cryptocurrencies']:,}\n"
                )
                
                await query.message.reply_text(market_text, parse_mode=ParseMode.MARKDOWN)
                return
        except Exception as e:
            logger.error(f"Market overview error: {e}")
        
        await query.message.reply_text("💹 Couldn't fetch market data. Try again!")
    
    # Command handlers
    async def imagine_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate AI image from prompt"""
        if not context.args:
            await update.message.reply_text("🎨 Usage: /imagine <your description>")
            return
        
        prompt = " ".join(context.args)
        await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
        
        try:
            encoded_prompt = urllib.parse.quote(prompt)
            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
            
            await update.message.reply_photo(
                photo=image_url,
                caption=f"🎨 *Generated Image*\n\nPrompt: _{prompt}_",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            await update.message.reply_text("❌ Failed to generate image. Try again!")
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Ask AI a question"""
        if not context.args:
            await update.message.reply_text("💬 Usage: /ask <your question>")
            return
        
        question = " ".join(context.args)
        await update.message.reply_chat_action(ChatAction.TYPING)
        
        try:
            encoded_question = urllib.parse.quote(question)
            response = requests.get(
                f"https://text.pollinations.ai/{encoded_question}",
                timeout=30
            )
            
            if response.status_code == 200:
                answer = response.text
                response_text = f"🤖 *AI Response*\n\n{answer}"
                
                # Split long messages
                if len(response_text) > 4000:
                    response_text = response_text[:4000] + "..."
                
                await update.message.reply_text(response_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text("❌ AI service unavailable. Try again later!")
        except Exception as e:
            logger.error(f"AI chat error: {e}")
            await update.message.reply_text("❌ Failed to get AI response. Try again!")
    
    async def weather_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get weather for a city"""
        if not context.args:
            await update.message.reply_text("🌤️ Usage: /weather <city name>")
            return
        
        city = " ".join(context.args)
        await update.message.reply_chat_action(ChatAction.TYPING)
        
        try:
            # Geocoding to get coordinates
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
            geo_response = requests.get(geo_url, timeout=10)
            
            if geo_response.status_code == 200 and geo_response.json().get('results'):
                location = geo_response.json()['results'][0]
                lat = location['latitude']
                lon = location['longitude']
                
                # Get weather data
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code&timezone=auto"
                weather_response = requests.get(weather_url, timeout=10)
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()['current']
                    
                    weather_codes = {
                        0: "☀️ Clear sky",
                        1: "🌤️ Mainly clear",
                        2: "⛅ Partly cloudy",
                        3: "☁️ Overcast",
                        45: "🌫️ Foggy",
                        48: "🌫️ Foggy",
                        51: "🌦️ Light drizzle",
                        61: "🌧️ Light rain",
                        71: "🌨️ Light snow",
                        95: "⛈️ Thunderstorm"
                    }
                    
                    weather_desc = weather_codes.get(weather_data['weather_code'], "🌡️ Weather")
                    
                    weather_text = (
                        f"🌤️ *Weather in {location['name']}, {location['country']}*\n\n"
                        f"{weather_desc}\n\n"
                        f"🌡️ Temperature: {weather_data['temperature_2m']}°C\n"
                        f"💧 Humidity: {weather_data['relative_humidity_2m']}%\n"
                        f"💨 Wind Speed: {weather_data['wind_speed_10m']} km/h"
                    )
                    
                    await update.message.reply_text(weather_text, parse_mode=ParseMode.MARKDOWN)
                    return
            
            await update.message.reply_text(f"❌ City '{city}' not found. Try again!")
        except Exception as e:
            logger.error(f"Weather error: {e}")
            await update.message.reply_text("❌ Failed to fetch weather. Try again!")
    
    async def crypto_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get cryptocurrency price"""
        if not context.args:
            await update.message.reply_text("📊 Usage: /crypto <symbol> (e.g., /crypto btc)")
            return
        
        symbol = context.args[0].lower()
        await update.message.reply_chat_action(ChatAction.TYPING)
        
        crypto_map = {
            'btc': 'bitcoin',
            'eth': 'ethereum',
            'doge': 'dogecoin',
            'ada': 'cardano',
            'xrp': 'ripple',
            'dot': 'polkadot',
            'sol': 'solana',
            'matic': 'polygon',
            'link': 'chainlink',
            'ltc': 'litecoin'
        }
        
        crypto_id = crypto_map.get(symbol, symbol)
        
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd&include_24hr_change=true&include_market_cap=true"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200 and crypto_id in response.json():
                data = response.json()[crypto_id]
                
                change_emoji = "📈" if data.get('usd_24h_change', 0) > 0 else "📉"
                change_sign = "+" if data.get('usd_24h_change', 0) > 0 else ""
                
                crypto_text = (
                    f"📊 *{crypto_id.upper()}*\n\n"
                    f"💵 Price: ${data['usd']:,.4f}\n"
                    f"{change_emoji} 24h: {change_sign}{data.get('usd_24h_change', 0):.2f}%\n"
                    f"📊 Market Cap: ${data.get('usd_market_cap', 0):,.0f}"
                )
                
                await update.message.reply_text(crypto_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(f"❌ Cryptocurrency '{symbol}' not found!")
        except Exception as e:
            logger.error(f"Crypto command error: {e}")
            await update.message.reply_text("❌ Failed to fetch crypto data. Try again!")
    
    async def meme_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send random meme"""
        await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
        
        try:
            response = requests.get("https://meme-api.com/gimme", timeout=10)
            if response.status_code == 200:
                data = response.json()
                await update.message.reply_photo(
                    photo=data['url'],
                    caption=f"😂 *{data['title']}*\n\n👍 {data.get('ups', 0)} upvotes",
                    parse_mode=ParseMode.MARKDOWN
                )
        except Exception as e:
            logger.error(f"Meme command error: {e}")
            await update.message.reply_text("😅 Couldn't fetch a meme. Try again!")
    
    async def joke_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send random joke"""
        try:
            headers = {'Accept': 'application/json'}
            response = requests.get("https://icanhazdadjoke.com/", headers=headers, timeout=10)
            
            if response.status_code == 200:
                joke = response.json()['joke']
                await update.message.reply_text(f"🎭 {joke}")
        except Exception as e:
            logger.error(f"Joke command error: {e}")
            await update.message.reply_text("😅 Couldn't fetch a joke. Try again!")
    
    async def quote_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Send inspirational quote"""
        try:
            response = requests.get("https://api.quotable.io/random", timeout=10)
            if response.status_code == 200:
                data = response.json()
                quote_text = f"💭 _{data['content']}_\n\n— *{data['author']}*"
                await update.message.reply_text(quote_text, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            logger.error(f"Quote command error: {e}")
            await update.message.reply_text("💭 Couldn't fetch a quote. Try again!")
    
    async def qr_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Generate QR code"""
        if not context.args:
            await update.message.reply_text("📱 Usage: /qr <text or URL>")
            return
        
        text = " ".join(context.args)
        await update.message.reply_chat_action(ChatAction.UPLOAD_PHOTO)
        
        try:
            encoded_text = urllib.parse.quote(text)
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=500x500&data={encoded_text}"
            
            await update.message.reply_photo(
                photo=qr_url,
                caption=f"📱 *QR Code Generated*\n\nData: `{text}`",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"QR code error: {e}")
            await update.message.reply_text("❌ Failed to generate QR code. Try again!")
    
    async def book_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for books"""
        if not context.args:
            await update.message.reply_text("📚 Usage: /book <title>")
            return
        
        query = " ".join(context.args)
        await update.message.reply_chat_action(ChatAction.TYPING)
        
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://openlibrary.org/search.json?q={encoded_query}&limit=5"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('docs'):
                    books_text = f"📚 *Search results for '{query}'*\n\n"
                    
                    for i, book in enumerate(data['docs'][:5], 1):
                        title = book.get('title', 'Unknown')
                        author = ', '.join(book.get('author_name', ['Unknown']))
                        year = book.get('first_publish_year', 'N/A')
                        
                        books_text += f"{i}. *{title}*\n"
                        books_text += f"   Author: {author}\n"
                        books_text += f"   Year: {year}\n\n"
                    
                    await update.message.reply_text(books_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text(f"❌ No books found for '{query}'")
        except Exception as e:
            logger.error(f"Book search error: {e}")
            await update.message.reply_text("❌ Failed to search books. Try again!")
    
    async def country_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get country information"""
        if not context.args:
            await update.message.reply_text("🌍 Usage: /country <country name>")
            return
        
        country = " ".join(context.args)
        await update.message.reply_chat_action(ChatAction.TYPING)
        
        try:
            encoded_country = urllib.parse.quote(country)
            url = f"https://restcountries.com/v3.1/name/{encoded_country}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()[0]
                
                country_text = (
                    f"🌍 *{data['name']['common']}*\n\n"
                    f"🏛️ Capital: {data.get('capital', ['N/A'])[0]}\n"
                    f"👥 Population: {data.get('population', 0):,}\n"
                    f"🗺️ Region: {data.get('region', 'N/A')}\n"
                    f"💬 Languages: {', '.join(data.get('languages', {}).values())}\n"
                    f"💰 Currency: {', '.join([c.get('name', 'N/A') for c in data.get('currencies', {}).values()])}\n"
                    f"🌐 TLD: {', '.join(data.get('tld', ['N/A']))}\n"
                    f"{data.get('flag', '🏴')} Flag"
                )
                
                await update.message.reply_text(country_text, parse_mode=ParseMode.MARKDOWN)
            else:
                await update.message.reply_text(f"❌ Country '{country}' not found!")
        except Exception as e:
            logger.error(f"Country info error: {e}")
            await update.message.reply_text("❌ Failed to fetch country info. Try again!")
    
    async def convert_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Convert currency"""
        if len(context.args) < 3:
            await update.message.reply_text("💱 Usage: /convert <amount> <from> <to>\nExample: /convert 100 USD EUR")
            return
        
        try:
            amount = float(context.args[0])
            from_curr = context.args[1].upper()
            to_curr = context.args[2].upper()
            
            await update.message.reply_chat_action(ChatAction.TYPING)
            
            url = f"https://api.exchangerate.host/latest?base={from_curr}&symbols={to_curr}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success') and to_curr in data.get('rates', {}):
                    rate = data['rates'][to_curr]
                    result = amount * rate
                    
                    convert_text = (
                        f"💱 *Currency Conversion*\n\n"
                        f"{amount:,.2f} {from_curr} = {result:,.2f} {to_curr}\n\n"
                        f"📊 Rate: 1 {from_curr} = {rate:.4f} {to_curr}"
                    )
                    
                    await update.message.reply_text(convert_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Invalid currency codes!")
            else:
                await update.message.reply_text("❌ Failed to fetch exchange rates!")
        except ValueError:
            await update.message.reply_text("❌ Invalid amount! Use numbers only.")
        except Exception as e:
            logger.error(f"Currency conversion error: {e}")
            await update.message.reply_text("❌ Failed to convert currency. Try again!")
    
    # Admin commands
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show bot statistics (admin only)"""
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("❌ Admin access required!")
            return
        
        uptime = datetime.now() - self.bot_stats['start_time']
        hours = uptime.total_seconds() / 3600
        
        stats_text = (
            f"📊 *Bot Statistics*\n\n"
            f"👥 Total Users: {len(self.users)}\n"
            f"💬 Total Commands: {self.bot_stats['total_commands']}\n"
            f"⏱️ Uptime: {int(hours)}h {int((hours % 1) * 60)}m\n"
            f"📅 Started: {self.bot_stats['start_time'].strftime('%Y-%m-%d %H:%M')}\n\n"
            f"*Top Features:*\n"
        )
        
        # Top 5 features
        sorted_features = sorted(
            self.bot_stats['features_used'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        for feature, count in sorted_features:
            stats_text += f"• {feature}: {count}\n"
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)
    
    async def broadcast_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users (admin only)"""
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("❌ Admin access required!")
            return
        
        if not context.args:
            await update.message.reply_text("📢 Usage: /broadcast <message>")
            return
        
        message = " ".join(context.args)
        success = 0
        failed = 0
        
        await update.message.reply_text(f"📢 Broadcasting to {len(self.users)} users...")
        
        for user_id in self.users.keys():
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 *Broadcast Message*\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
                success += 1
                await asyncio.sleep(0.05)  # Rate limiting
            except Exception as e:
                logger.error(f"Broadcast error for user {user_id}: {e}")
                failed += 1
        
        await update.message.reply_text(
            f"✅ Broadcast complete!\n\n"
            f"Sent: {success}\nFailed: {failed}"
        )
    
    async def users_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """List all users (admin only)"""
        if update.effective_user.id != self.admin_id:
            await update.message.reply_text("❌ Admin access required!")
            return
        
        users_text = f"👥 *Total Users: {len(self.users)}*\n\n"
        
        for user_id, user_data in list(self.users.items())[:20]:
            users_text += f"• {user_data.get('username', 'N/A')} (ID: {user_id})\n"
        
        if len(self.users) > 20:
            users_text += f"\n... and {len(self.users) - 20} more"
        
        await update.message.reply_text(users_text, parse_mode=ParseMode.MARKDOWN)
    
    # Group handlers
    async def new_member_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Welcome new members"""
        for member in update.message.new_chat_members:
            if member.id == context.bot.id:
                # Bot was added to group
                welcome_msg = (
                    f"👋 Thanks for adding me to *{update.effective_chat.title}*!\n\n"
                    f"I'll help make this group awesome with:\n"
                    f"• Auto-welcome messages\n"
                    f"• Fun commands and entertainment\n"
                    f"• Useful utilities\n\n"
                    f"Use /help to see what I can do!"
                )
                await update.message.reply_text(welcome_msg, parse_mode=ParseMode.MARKDOWN)
            else:
                # Regular member joined
                welcome_msg = (
                    f"👋 Welcome {member.mention_html()}, to *{update.effective_chat.title}*!\n\n"
                    f"We're glad to have you here! 🎉"
                )
                await update.message.reply_html(welcome_msg)
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Log errors"""
        logger.error(f"Update {update} caused error {context.error}")
    
    def run(self):
        """Start the bot"""
        app = Application.builder().token(self.token).build()
        
        # Command handlers
        app.add_handler(CommandHandler("start", self.start_command))
        app.add_handler(CommandHandler("help", self.help_command))
        app.add_handler(CommandHandler("imagine", self.imagine_command))
        app.add_handler(CommandHandler("ask", self.ask_command))
        app.add_handler(CommandHandler("weather", self.weather_command))
        app.add_handler(CommandHandler("crypto", self.crypto_command))
        app.add_handler(CommandHandler("btc", lambda u, c: self.crypto_command(u, type('obj', (object,), {'args': ['btc']})(), )))
        app.add_handler(CommandHandler("eth", lambda u, c: self.crypto_command(u, type('obj', (object,), {'args': ['eth']})(), )))
        app.add_handler(CommandHandler("doge", lambda u, c: self.crypto_command(u, type('obj', (object,), {'args': ['doge']})(), )))
        app.add_handler(CommandHandler("meme", self.meme_command))
        app.add_handler(CommandHandler("joke", self.joke_command))
        app.add_handler(CommandHandler("quote", self.quote_command))
        app.add_handler(CommandHandler("qr", self.qr_command))
        app.add_handler(CommandHandler("book", self.book_command))
        app.add_handler(CommandHandler("country", self.country_command))
        app.add_handler(CommandHandler("convert", self.convert_command))
        
        # Admin commands
        app.add_handler(CommandHandler("stats", self.stats_command))
        app.add_handler(CommandHandler("broadcast", self.broadcast_command))
        app.add_handler(CommandHandler("users", self.users_command))
        
        # Callback handlers
        app.add_handler(CallbackQueryHandler(self.button_callback))
        
        # Message handlers
        app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_menu_button
        ))
        
        # Group handlers
        app.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self.new_member_handler
        ))
        
        # Error handler
        app.add_error_handler(self.error_handler)
        
        logger.info("🚀 Advay Universe Bot is starting...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point"""
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = os.getenv("ADMIN_ID")
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN not found in environment variables!")
        return
    
    if not ADMIN_ID:
        logger.warning("⚠️ ADMIN_ID not set. Admin features will be disabled.")
    
    bot = AdvayUniverseBot(BOT_TOKEN, ADMIN_ID)
    bot.run()


if __name__ == "__main__":
    main()
