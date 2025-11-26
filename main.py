import os
import logging
import json
import random
import asyncio
from datetime import datetime, timedelta
import requests
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BotCommand
)
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    ContextTypes,
    CallbackQueryHandler,
    ConversationHandler
)
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')

# Store user data and group data (in production, use a database)
user_sessions = {}
group_settings = {}

# Conversation states
PROMPT_IMAGE, PROMPT_TEXT, WEATHER_LOCATION, BROADCAST_MESSAGE, URL_SHORTEN, BOOK_SEARCH, REMINDER_SET, CURRENCY_CONVERT = range(8)

class AdvayUniverseBot:
    def __init__(self):
        self.application = None
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat_type = update.effective_chat.type
        
        if chat_type == "private":
            welcome_text = f"""
🌟 *Welcome to Advay Universe, {user.first_name}!* 🌟

I'm your all-in-one AI assistant with amazing features:

🤖 *AI Features*
• Generate AI images from text
• AI text generation and completion
• Smart conversations

🎉 *Entertainment*
• Memes from various subreddits
• Random jokes & quotes
• Animal images & facts
• Comics & fun content

💰 *Utilities*
• Currency conversion
• Weather forecasts
• URL shortener
• QR code generator
• Book searches

🌐 *Group Features*
• Welcome messages
• Auto-responses
• Group management tools

Use the menu below or type /help for more info!
            """
            
            keyboard = [
                [KeyboardButton("🤖 AI Features"), KeyboardButton("🎉 Entertainment")],
                [KeyboardButton("💰 Utilities"), KeyboardButton("🌐 Group Tools")],
                [KeyboardButton("⚙️ Admin Panel"), KeyboardButton("ℹ️ Help")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            await update.message.reply_text(
                welcome_text,
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Track user
            if user.id not in user_sessions:
                user_sessions[user.id] = {
                    'first_seen': datetime.now(),
                    'usage_count': 0,
                    'preferences': {}
                }
        else:
            await update.message.reply_text(
                "🤖 Advay Universe is here! I'm ready to assist in this group. "
                "Type /help to see what I can do!",
                parse_mode=ParseMode.MARKDOWN
            )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        help_text = """
📚 *Advay Universe Bot Help*

*Basic Commands:*
/start - Start the bot
/help - Show this help message
/menu - Show main menu

*AI Features:*
/ai_image - Generate AI image from text
/ai_text - Generate AI text completion
/chat - Have a conversation with AI

*Entertainment:*
/meme - Get random memes
/joke - Get random jokes
/quote - Get inspirational quotes
/cat - Random cat images
/dog - Random dog images
/comic - Random xkcd comic

*Utilities:*
/weather - Get weather information
/currency - Currency converter
/shorten - Shorten URLs
/qr - Generate QR codes
/book - Search for books
/reminder - Set reminders

*Group Features:*
/welcome - Configure welcome messages
/rules - Set group rules
/stats - Group statistics

*Admin Commands:*
/broadcast - Broadcast message to all users
/stats - Bot usage statistics
/export - Export user data

Use buttons or commands to interact with me! 🚀
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Track usage
        if user_id in user_sessions:
            user_sessions[user_id]['usage_count'] += 1
        
        if user_message == "🤖 AI Features":
            await self.show_ai_features(update, context)
        elif user_message == "🎉 Entertainment":
            await self.show_entertainment(update, context)
        elif user_message == "💰 Utilities":
            await self.show_utilities(update, context)
        elif user_message == "🌐 Group Tools":
            await self.show_group_tools(update, context)
        elif user_message == "⚙️ Admin Panel":
            await self.show_admin_panel(update, context)
        elif user_message == "ℹ️ Help":
            await self.help_command(update, context)
        else:
            # AI response for general messages
            response = await self.generate_ai_response(user_message)
            await update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

    async def show_ai_features(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [
                InlineKeyboardButton("🖼️ Generate Image", callback_data="ai_image"),
                InlineKeyboardButton("📝 AI Text", callback_data="ai_text")
            ],
            [
                InlineKeyboardButton("🤖 Chat Completion", callback_data="ai_chat"),
                InlineKeyboardButton("🎨 Creative Writing", callback_data="creative_write")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 *AI Features Menu*\n\nChoose an AI feature to use:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_entertainment(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [
                InlineKeyboardButton("😂 Memes", callback_data="get_meme"),
                InlineKeyboardButton("😄 Jokes", callback_data="get_joke")
            ],
            [
                InlineKeyboardButton("💬 Quotes", callback_data="get_quote"),
                InlineKeyboardButton("🐱 Animals", callback_data="get_animal")
            ],
            [
                InlineKeyboardButton("📚 Comics", callback_data="get_comic"),
                InlineKeyboardButton("🎮 Activities", callback_data="get_activity")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🎉 *Entertainment Menu*\n\nChoose entertainment option:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_utilities(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [
                InlineKeyboardButton("🌤️ Weather", callback_data="get_weather"),
                InlineKeyboardButton("💰 Currency", callback_data="currency_convert")
            ],
            [
                InlineKeyboardButton("🔗 URL Shortener", callback_data="shorten_url"),
                InlineKeyboardButton("📱 QR Code", callback_data="generate_qr")
            ],
            [
                InlineKeyboardButton("📚 Book Search", callback_data="search_book"),
                InlineKeyboardButton("⏰ Reminder", callback_data="set_reminder")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💰 *Utilities Menu*\n\nChoose a utility:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_group_tools(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [
                InlineKeyboardButton("👋 Welcome Setup", callback_data="setup_welcome"),
                InlineKeyboardButton("📊 Group Stats", callback_data="group_stats")
            ],
            [
                InlineKeyboardButton("📝 Rules", callback_data="group_rules"),
                InlineKeyboardButton("🎯 Auto-Reply", callback_data="auto_reply")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🌐 *Group Tools*\n\nConfigure group features:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Access denied. Admin only.")
            return
            
        total_users = len(user_sessions)
        keyboard = [
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
                InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton("📤 Export Data", callback_data="admin_export"),
                InlineKeyboardButton("🔄 System Info", callback_data="system_info")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"⚙️ *Admin Panel*\n\nTotal Users: {total_users}\n\nAdmin tools:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            await self.start(update, context)
            
        elif data == "ai_image":
            await query.edit_message_text(
                "🖼️ *AI Image Generation*\n\nSend me a description of the image you want to generate:",
                parse_mode=ParseMode.MARKDOWN
            )
            return PROMPT_IMAGE
            
        elif data == "ai_text":
            await query.edit_message_text(
                "📝 *AI Text Generation*\n\nSend me a prompt for text generation:",
                parse_mode=ParseMode.MARKDOWN
            )
            return PROMPT_TEXT
            
        elif data == "get_meme":
            meme = await self.get_random_meme()
            await query.edit_message_text(meme, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_joke":
            joke = await self.get_random_joke()
            await query.edit_message_text(joke, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_quote":
            quote = await self.get_random_quote()
            await query.edit_message_text(quote, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_animal":
            animal = await self.get_random_animal()
            await query.edit_message_text(animal, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_weather":
            await query.edit_message_text(
                "🌤️ *Weather Information*\n\nSend me a city name:",
                parse_mode=ParseMode.MARKDOWN
            )
            return WEATHER_LOCATION
            
        elif data == "currency_convert":
            await query.edit_message_text(
                "💰 *Currency Converter*\n\nSend amount and currencies (e.g., 100 USD to KES):",
                parse_mode=ParseMode.MARKDOWN
            )
            return CURRENCY_CONVERT

    # AI Image Generation
    async def generate_ai_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        prompt = update.message.text
        
        try:
            await update.message.reply_text("🖼️ Generating your image...")
            
            # Use pollinations.ai for image generation
            url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
            
            # Send the image
            await update.message.reply_photo(
                photo=url,
                caption=f"🖼️ *Generated Image*\n\nPrompt: {prompt}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating image: {str(e)}")
        
        return ConversationHandler.END

    # AI Text Generation
    async def generate_ai_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        prompt = update.message.text
        
        try:
            await update.message.reply_text("🤖 Generating text...")
            
            # Use pollinations.ai for text generation
            url = f"https://pollinations.ai/api/text?prompt={requests.utils.quote(prompt)}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                text_response = response.text
                await update.message.reply_text(
                    f"📝 *AI Response*\n\n{text_response}",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await update.message.reply_text("❌ Failed to generate text response")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating text: {str(e)}")
        
        return ConversationHandler.END

    # Entertainment Features
    async def get_random_meme(self) -> str:
        try:
            # Try multiple meme APIs
            apis = [
                "https://meme-api.com/gimme/1",
                "https://some-random-api.ml/meme"
            ]
            
            for api in apis:
                try:
                    response = requests.get(api, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'url' in data:
                            return f"😂 *Random Meme*\n\n[View Image]({data['url']})"
                        elif 'memes' in data and len(data['memes']) > 0:
                            meme = data['memes'][0]
                            return f"😂 *Random Meme*\n\nTitle: {meme.get('title', 'Unknown')}\n[View Image]({meme['url']})"
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Meme error: {e}")
            
        return "❌ Could not fetch meme at this time"

    async def get_random_joke(self) -> str:
        try:
            apis = [
                "https://icanhazdadjoke.com/",
                "https://v2.jokeapi.dev/joke/Programming,Any?type=single"
            ]
            
            for api in apis:
                try:
                    headers = {'Accept': 'application/json'} if 'icanhazdadjoke' in api else {}
                    response = requests.get(api, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'joke' in data:
                            return f"😄 *Joke*\n\n{data['joke']}"
                        elif 'joke' in data:  # jokeapi
                            return f"😄 *Joke*\n\n{data['joke']}"
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Joke error: {e}")
            
        return "❌ Could not fetch joke at this time"

    async def get_random_quote(self) -> str:
        try:
            apis = [
                "https://api.quotable.io/random",
                "https://programming-quotes-api.herokuapp.com/quotes/random",
                "https://api.adviceslip.com/advice"
            ]
            
            for api in apis:
                try:
                    response = requests.get(api, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'content' in data and 'author' in data:  # quotable.io
                            return f"💬 *Quote*\n\n\"{data['content']}\"\n\n— {data['author']}"
                        elif 'en' in data:  # programming-quotes
                            return f"💬 *Programming Quote*\n\n\"{data['en']}\"\n\n— {data.get('author', 'Unknown')}"
                        elif 'slip' in data:  # advice slip
                            return f"💡 *Advice*\n\n{data['slip']['advice']}"
                except:
                    continue
                    
        except Exception as e:
            logger.error(f"Quote error: {e}")
            
        return "❌ Could not fetch quote at this time"

    async def get_random_animal(self) -> str:
        try:
            animals = [
                ("🐕 Dog", "https://dog.ceo/api/breeds/image/random"),
                ("🐈 Cat", "https://api.thecatapi.com/v1/images/search"),
                ("🐕 Shiba", "http://shibe.online/api/shibes?count=1")
            ]
            
            animal_name, api = random.choice(animals)
            response = requests.get(api, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if animal_name == "🐕 Dog":
                    return f"{animal_name} Image\n\n[View Image]({data['message']})"
                elif animal_name == "🐈 Cat":
                    return f"{animal_name} Image\n\n[View Image]({data[0]['url']})"
                elif animal_name == "🐕 Shiba":
                    return f"{animal_name} Image\n\n[View Image]({data[0]})"
                    
        except Exception as e:
            logger.error(f"Animal error: {e}")
            
        return "❌ Could not fetch animal image at this time"

    # Weather Feature
    async def get_weather(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        location = update.message.text
        
        try:
            # First, get coordinates from location name
            geo_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(location)}&format=json"
            geo_response = requests.get(geo_url, timeout=10)
            
            if geo_response.status_code == 200 and geo_response.json():
                geo_data = geo_response.json()[0]
                lat, lon = geo_data['lat'], geo_data['lon']
                
                # Get weather data
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                weather_response = requests.get(weather_url, timeout=10)
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    current = weather_data['current_weather']
                    
                    temp = current['temperature']
                    windspeed = current['windspeed']
                    weather_code = current['weathercode']
                    
                    # Simple weather description based on code
                    weather_desc = self.get_weather_description(weather_code)
                    
                    weather_text = f"""
🌤️ *Weather in {location}*

📍 Coordinates: {lat}, {lon}
🌡️ Temperature: {temp}°C
💨 Wind Speed: {windspeed} km/h
☁️ Conditions: {weather_desc}
                    """
                    
                    await update.message.reply_text(weather_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Could not fetch weather data")
            else:
                await update.message.reply_text("❌ Location not found")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error fetching weather: {str(e)}")
        
        return ConversationHandler.END

    def get_weather_description(self, code: int) -> str:
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            48: "Depositing rime fog",
            51: "Light drizzle",
            53: "Moderate drizzle",
            55: "Dense drizzle",
            61: "Slight rain",
            63: "Moderate rain",
            65: "Heavy rain",
            80: "Slight rain showers",
            81: "Moderate rain showers",
            82: "Violent rain showers"
        }
        return weather_codes.get(code, "Unknown")

    # Currency Converter
    async def convert_currency(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text.upper()
        
        try:
            # Parse input like "100 USD to KES"
            parts = text.split()
            if len(parts) >= 4 and parts[1] and parts[3]:
                amount = float(parts[0])
                from_curr = parts[1]
                to_curr = parts[3]
                
                url = f"https://api.exchangerate.host/convert?from={from_curr}&to={to_curr}&amount={amount}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['success']:
                        result = data['result']
                        rate = data['info']['rate']
                        
                        conversion_text = f"""
💰 *Currency Conversion*

💵 {amount} {from_curr} = {result:.2f} {to_curr}
📊 Exchange Rate: 1 {from_curr} = {rate:.4f} {to_curr}
                        """
                        
                        await update.message.reply_text(conversion_text, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await update.message.reply_text("❌ Currency conversion failed")
                else:
                    await update.message.reply_text("❌ Could not fetch exchange rates")
            else:
                await update.message.reply_text("❌ Invalid format. Use: '100 USD to KES'")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error converting currency: {str(e)}")
        
        return ConversationHandler.END

    # AI Response Generator
    async def generate_ai_response(self, prompt: str) -> str:
        try:
            # Enhanced AI response using multiple approaches
            if any(word in prompt.lower() for word in ['hello', 'hi', 'hey']):
                return f"👋 Hello! I'm Advay Universe! How can I assist you today?"
            elif any(word in prompt.lower() for word in ['weather', 'temperature']):
                return "🌤️ Want weather info? Use the Utilities menu or type /weather!"
            elif any(word in prompt.lower() for word in ['joke', 'funny']):
                joke = await self.get_random_joke()
                return joke
            elif any(word in prompt.lower() for word in ['quote', 'inspiration']):
                quote = await self.get_random_quote()
                return quote
            else:
                # Use pollinations.ai for general responses
                url = f"https://pollinations.ai/api/text?prompt={requests.utils.quote(prompt)}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    return f"🤖 {response.text}"
                else:
                    return "I'm here to help! Use the menu buttons to explore my features! 🚀"
                    
        except Exception as e:
            return "I'm Advay Universe! Use the menu to explore my amazing features! 🌟"

    # Group welcome handler
    async def welcome_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    # Bot was added to group
                    welcome_text = """
🤖 *Advay Universe has joined the group!*

I'm your multi-functional assistant! Here's what I can do:

🎉 Entertainment: memes, jokes, quotes
💰 Utilities: weather, currency, reminders
🤖 AI: image generation, text completion
📊 Group: stats, welcome messages

Use /help to see all commands!
                    """
                    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    # Regular user joined
                    welcome_text = f"""
👋 Welcome {member.first_name} to the group!

I'm Advay Universe, your group assistant. 
Type /help to see what I can do! 🚀
                    """
                    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)

    # Admin broadcast feature
    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Admin only feature")
            return ConversationHandler.END
            
        await update.message.reply_text(
            "📢 *Admin Broadcast*\n\nSend the message you want to broadcast to all users:",
            parse_mode=ParseMode.MARKDOWN
        )
        return BROADCAST_MESSAGE

    async def execute_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        message = update.message.text
        successful = 0
        failed = 0
        
        await update.message.reply_text("🔄 Starting broadcast...")
        
        for user_id in user_sessions.keys():
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 *Broadcast from Admin*\n\n{message}",
                    parse_mode=ParseMode.MARKDOWN
                )
                successful += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                failed += 1
                logger.error(f"Broadcast failed for {user_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Broadcast completed!\n\n✅ Successful: {successful}\n❌ Failed: {failed}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END

    # Crypto price checker
    async def crypto_price(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        try:
            coins = ['bitcoin', 'ethereum', 'dogecoin']
            prices_text = "💰 *Crypto Prices*\n\n"
            
            for coin in coins:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    price = data[coin]['usd']
                    prices_text += f"• {coin.title()}: ${price:,.2f}\n"
            
            await update.message.reply_text(prices_text, parse_mode=ParseMode.MARKDOWN)
            
        except Exception as e:
            await update.message.reply_text("❌ Could not fetch crypto prices")

    # Book search
    async def search_books(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text(
            "📚 *Book Search*\n\nSend me a book title or author to search:",
            parse_mode=ParseMode.MARKDOWN
        )
        return BOOK_SEARCH

    async def execute_book_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        query = update.message.text
        
        try:
            url = f"https://openlibrary.org/search.json?q={requests.utils.quote(query)}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                books = data.get('docs', [])[:5]  # Get first 5 results
                
                if books:
                    books_text = "📚 *Search Results*\n\n"
                    for i, book in enumerate(books, 1):
                        title = book.get('title', 'Unknown Title')
                        author = book.get('author_name', ['Unknown Author'])[0]
                        year = book.get('first_publish_year', 'Unknown')
                        
                        books_text += f"{i}. *{title}*\n   👤 {author}\n   📅 {year}\n\n"
                    
                    await update.message.reply_text(books_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ No books found")
            else:
                await update.message.reply_text("❌ Search failed")
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error searching books: {str(e)}")
        
        return ConversationHandler.END

    # Cancel conversation
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END

    def setup_handlers(self, application: Application) -> None:
        # Basic commands
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("crypto", self.crypto_price))
        
        # Message handler for buttons
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Button callback handler
        application.add_handler(CallbackQueryHandler(self.button_handler))
        
        # Group welcome handler
        application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, self.welcome_new_member))
        
        # Conversation handlers
        conv_handler_ai_image = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern="^ai_image$")],
            states={
                PROMPT_IMAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_ai_image)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        conv_handler_ai_text = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern="^ai_text$")],
            states={
                PROMPT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_ai_text)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        conv_handler_weather = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern="^get_weather$")],
            states={
                WEATHER_LOCATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_weather)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        conv_handler_currency = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern="^currency_convert$")],
            states={
                CURRENCY_CONVERT: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.convert_currency)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        conv_handler_broadcast = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.admin_broadcast, pattern="^admin_broadcast$")],
            states={
                BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.execute_broadcast)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        conv_handler_books = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.search_books, pattern="^search_book$")],
            states={
                BOOK_SEARCH: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.execute_book_search)]
            },
            fallbacks=[CommandHandler("cancel", self.cancel)]
        )
        
        application.add_handler(conv_handler_ai_image)
        application.add_handler(conv_handler_ai_text)
        application.add_handler(conv_handler_weather)
        application.add_handler(conv_handler_currency)
        application.add_handler(conv_handler_broadcast)
        application.add_handler(conv_handler_books)

    async def post_init(self, application: Application) -> None:
        # Set bot commands
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help"),
            BotCommand("menu", "Show main menu"),
            BotCommand("meme", "Get random meme"),
            BotCommand("joke", "Get random joke"),
            BotCommand("weather", "Get weather info"),
            BotCommand("crypto", "Crypto prices"),
        ]
        await application.bot.set_my_commands(commands)

    def run(self):
        """Run the bot"""
        application = Application.builder().token(BOT_TOKEN).post_init(self.post_init).build()
        self.application = application
        
        self.setup_handlers(application)
        
        logger.info("🤖 Advay Universe Bot is starting...")
        application.run_polling()

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is required!")
        return
    
    bot = AdvayUniverseBot()
    bot.run()

if __name__ == "__main__":
    main()
