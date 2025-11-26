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

# Store user data and group data
user_sessions = {}
group_settings = {}

# Conversation states
PROMPT_IMAGE, PROMPT_TEXT, WEATHER_LOCATION, BROADCAST_MESSAGE, URL_SHORTEN, BOOK_SEARCH, REMINDER_SET, CURRENCY_CONVERT, QR_GENERATE = range(9)

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
• Crypto prices

🌐 *Group Features*
• Welcome messages
• Auto-responses
• Group management tools

Use the menu below or type /help for more info!
            """
            
            keyboard = [
                [KeyboardButton("🤖 AI Features"), KeyboardButton("🎉 Entertainment")],
                [KeyboardButton("💰 Utilities"), KeyboardButton("📊 Crypto & Finance")],
                [KeyboardButton("🌐 Group Tools"), KeyboardButton("⚙️ Admin Panel")],
                [KeyboardButton("ℹ️ Help")]
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
                    'preferences': {},
                    'last_active': datetime.now()
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
/crypto - Crypto prices

*Group Features:*
Automatically welcomes new members
Use /help in groups for group-specific commands

*Admin Commands:*
/broadcast - Broadcast message to all users
/stats - Bot usage statistics

Use buttons or commands to interact with me! 🚀
        """
        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_message = update.message.text
        user_id = update.effective_user.id
        
        # Track usage
        if user_id in user_sessions:
            user_sessions[user_id]['usage_count'] += 1
            user_sessions[user_id]['last_active'] = datetime.now()
        
        if user_message == "🤖 AI Features":
            await self.show_ai_features(update, context)
        elif user_message == "🎉 Entertainment":
            await self.show_entertainment(update, context)
        elif user_message == "💰 Utilities":
            await self.show_utilities(update, context)
        elif user_message == "📊 Crypto & Finance":
            await self.show_crypto_finance(update, context)
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
                InlineKeyboardButton("🎨 Creative Ideas", callback_data="creative_ideas"),
                InlineKeyboardButton("📚 Story Writer", callback_data="story_writer")
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
            [
                InlineKeyboardButton("🍕 Random Food", callback_data="random_food"),
                InlineKeyboardButton("🎲 Random Fact", callback_data="random_fact")
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
                InlineKeyboardButton("🌍 Country Info", callback_data="country_info")
            ],
            [
                InlineKeyboardButton("📰 News", callback_data="get_news"),
                InlineKeyboardButton("🕐 Time Info", callback_data="time_info")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "💰 *Utilities Menu*\n\nChoose a utility:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def show_crypto_finance(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        keyboard = [
            [
                InlineKeyboardButton("₿ Crypto Prices", callback_data="crypto_prices"),
                InlineKeyboardButton("💹 Bitcoin", callback_data="bitcoin_price")
            ],
            [
                InlineKeyboardButton("🪙 Ethereum", callback_data="ethereum_price"),
                InlineKeyboardButton("🐕 Dogecoin", callback_data="dogecoin_price")
            ],
            [
                InlineKeyboardButton("💰 Forex Rates", callback_data="forex_rates"),
                InlineKeyboardButton("📈 Stock Info", callback_data="stock_info")
            ],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="main_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📊 *Crypto & Finance*\n\nGet real-time crypto and financial data:",
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
        active_today = sum(1 for user_data in user_sessions.values() 
                          if (datetime.now() - user_data['last_active']).days < 1)
        
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
            f"⚙️ *Admin Panel*\n\n👥 Total Users: {total_users}\n🟢 Active Today: {active_today}\n\nAdmin tools:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == "main_menu":
            await query.edit_message_text("Returning to main menu...")
            await self.start(update, context)
            return
            
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
            await query.edit_message_text("🔄 Getting a fresh meme...")
            meme = await self.get_random_meme()
            await query.edit_message_text(meme, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_joke":
            await query.edit_message_text("🔄 Fetching a joke...")
            joke = await self.get_random_joke()
            await query.edit_message_text(joke, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_quote":
            await query.edit_message_text("🔄 Getting an inspirational quote...")
            quote = await self.get_random_quote()
            await query.edit_message_text(quote, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_animal":
            await query.edit_message_text("🔄 Finding a cute animal...")
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
            
        elif data == "generate_qr":
            await query.edit_message_text(
                "📱 *QR Code Generator*\n\nSend text or URL to convert to QR code:",
                parse_mode=ParseMode.MARKDOWN
            )
            return QR_GENERATE
            
        elif data == "crypto_prices":
            await query.edit_message_text("🔄 Fetching crypto prices...")
            prices = await self.get_crypto_prices()
            await query.edit_message_text(prices, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "bitcoin_price":
            price = await self.get_specific_crypto("bitcoin")
            await query.edit_message_text(price, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "ethereum_price":
            price = await self.get_specific_crypto("ethereum")
            await query.edit_message_text(price, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "dogecoin_price":
            price = await self.get_specific_crypto("dogecoin")
            await query.edit_message_text(price, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "random_food":
            food = await self.get_random_food()
            await query.edit_message_text(food, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "random_fact":
            fact = await self.get_random_fact()
            await query.edit_message_text(fact, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_comic":
            comic = await self.get_random_comic()
            await query.edit_message_text(comic, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "get_activity":
            activity = await self.get_random_activity()
            await query.edit_message_text(activity, parse_mode=ParseMode.MARKDOWN)
            
        elif data == "country_info":
            await query.edit_message_text(
                "🌍 *Country Information*\n\nSend me a country name:",
                parse_mode=ParseMode.MARKDOWN
            )
            # This would be implemented similarly to other features
            
        elif data == "admin_broadcast":
            user_id = query.from_user.id
            if user_id != ADMIN_ID:
                await query.edit_message_text("❌ Admin only feature")
                return
            await query.edit_message_text(
                "📢 *Admin Broadcast*\n\nSend the message you want to broadcast to all users:",
                parse_mode=ParseMode.MARKDOWN
            )
            return BROADCAST_MESSAGE

    # AI Image Generation
    async def generate_ai_image(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        prompt = update.message.text
        
        try:
            await update.message.reply_text("🎨 Generating your image... This may take a moment.")
            
            # Use pollinations.ai for image generation
            url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
            
            # Send the image
            await update.message.reply_photo(
                photo=url,
                caption=f"🖼️ *AI Generated Image*\n\nPrompt: {prompt}\n\nGenerated via Pollinations.ai",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating image: {str(e)}")
        
        return ConversationHandler.END

    # AI Text Generation
    async def generate_ai_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        prompt = update.message.text
        
        try:
            await update.message.reply_text("🤖 Generating text response...")
            
            # Use pollinations.ai for text generation
            url = f"https://pollinations.ai/api/text?prompt={requests.utils.quote(prompt)}"
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                text_response = response.text[:4000]  # Telegram message limit
                await update.message.reply_text(
                    f"📝 *AI Response*\n\n{text_response}\n\n---\n_Powered by Pollinations.ai_",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                # Fallback response
                fallback_responses = [
                    f"I understand you're asking about: {prompt}. That's an interesting topic!",
                    f"Regarding '{prompt}', I think this is worth exploring further.",
                    f"Your query about '{prompt}' is quite intriguing. Let me think about that...",
                    f"I've received your message about {prompt}. This seems important!"
                ]
                await update.message.reply_text(
                    f"🤖 {random.choice(fallback_responses)}\n\n_(Note: AI service temporarily unavailable)_",
                    parse_mode=ParseMode.MARKDOWN
                )
                
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating text: {str(e)}")
        
        return ConversationHandler.END

    # QR Code Generator
    async def generate_qr_code(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        text = update.message.text
        
        try:
            # Generate QR code
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={requests.utils.quote(text)}"
            
            await update.message.reply_photo(
                photo=qr_url,
                caption=f"📱 *QR Code Generated*\n\nContent: {text}",
                parse_mode=ParseMode.MARKDOWN
            )
            
        except Exception as e:
            await update.message.reply_text(f"❌ Error generating QR code: {str(e)}")
        
        return ConversationHandler.END

    # Entertainment Features
    async def get_random_meme(self) -> str:
        try:
            subreddits = ['memes', 'dankmemes', 'wholesomememes', 'me_irl']
            subreddit = random.choice(subreddits)
            
            url = f"https://meme-api.com/gimme/{subreddit}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return f"😂 *Meme from r/{data['subreddit']}*\n\n*{data['title']}*\n\n[View Image]({data['url']})"
            else:
                return "❌ Could not fetch meme. Try again later!"
                
        except Exception as e:
            logger.error(f"Meme error: {e}")
            return "❌ Error fetching meme. Please try again!"

    async def get_random_joke(self) -> str:
        try:
            apis = [
                "https://icanhazdadjoke.com/",
                "https://v2.jokeapi.dev/joke/Any?type=single"
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
                    
            return "🤡 Why don't scientists trust atoms?\n\nBecause they make up everything!"
                    
        except Exception as e:
            logger.error(f"Joke error: {e}")
            return "😄 Here's a joke: I told my computer I needed a break... now it won't stop sending me vacation ads!"

    async def get_random_quote(self) -> str:
        try:
            apis = [
                "https://api.quotable.io/random",
                "https://api.adviceslip.com/advice"
            ]
            
            for api in apis:
                try:
                    response = requests.get(api, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        
                        if 'content' in data and 'author' in data:  # quotable.io
                            return f"💬 *Inspirational Quote*\n\n\"{data['content']}\"\n\n— {data['author']}"
                        elif 'slip' in data:  # advice slip
                            return f"💡 *Helpful Advice*\n\n{data['slip']['advice']}"
                except:
                    continue
                    
            return "💬 The only way to do great work is to love what you do. - Steve Jobs"
                    
        except Exception as e:
            logger.error(f"Quote error: {e}")
            return "💬 Believe you can and you're halfway there. - Theodore Roosevelt"

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
                    return f"{animal_name} 🐾\n\n[View Cute Dog]({data['message']})"
                elif animal_name == "🐈 Cat":
                    return f"{animal_name} 🐾\n\n[View Cute Cat]({data[0]['url']})"
                elif animal_name == "🐕 Shiba":
                    return f"{animal_name} 🐾\n\n[View Cute Shiba]({data[0]})"
                    
            return "🐾 Couldn't fetch an animal image, but here's a virtual pet: 🐶"
                    
        except Exception as e:
            logger.error(f"Animal error: {e}")
            return "🐾 Animals are amazing! 🐱🐶"

    async def get_random_food(self) -> str:
        try:
            apis = [
                "https://www.themealdb.com/api/json/v1/1/random.php",
                "https://www.thecocktaildb.com/api/json/v1/1/random.php"
            ]
            
            api = random.choice(apis)
            response = requests.get(api, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'meals' in data and data['meals']:
                    meal = data['meals'][0]
                    return f"🍕 *Random Meal Idea*\n\n*{meal['strMeal']}*\nCategory: {meal['strCategory']}\nArea: {meal['strArea']}\n\n[View Recipe]({meal['strMealThumb']})"
                elif 'drinks' in data and data['drinks']:
                    drink = data['drinks'][0]
                    return f"🍹 *Random Drink Idea*\n\n*{drink['strDrink']}*\nCategory: {drink['strCategory']}\nAlcoholic: {drink['strAlcoholic']}\n\n[View Drink]({drink['strDrinkThumb']})"
                    
            return "🍕 Try making spaghetti carbonara tonight! 🍝"
                    
        except Exception as e:
            logger.error(f"Food error: {e}")
            return "🍕 Food is life! What's your favorite dish?"

    async def get_random_fact(self) -> str:
        try:
            url = f"http://numbersapi.com/{random.randint(1, 100)}/trivia?json"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return f"🎲 *Random Fact*\n\n{data['text']}"
            else:
                facts = [
                    "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
                    "Octopuses have three hearts.",
                    "A day on Venus is longer than a year on Venus.",
                    "Bananas are berries, but strawberries aren't.",
                    "The shortest war in history was between Britain and Zanzibar in 1896. Zanzibar surrendered after 38 minutes."
                ]
                return f"🎲 *Random Fact*\n\n{random.choice(facts)}"
                    
        except Exception as e:
            logger.error(f"Fact error: {e}")
            return "🎲 Did you know? The first computer mouse was made of wood!"

    async def get_random_comic(self) -> str:
        try:
            # Get latest comic number first
            response = requests.get("https://xkcd.com/info.0.json", timeout=10)
            if response.status_code == 200:
                data = response.json()
                latest_num = data['num']
                
                # Get random comic
                random_num = random.randint(1, latest_num)
                comic_response = requests.get(f"https://xkcd.com/{random_num}/info.0.json", timeout=10)
                
                if comic_response.status_code == 200:
                    comic_data = comic_response.json()
                    return f"📚 *xkcd Comic #{comic_data['num']}*\n\n*{comic_data['title']}*\n\n{comic_data['alt']}\n\n[View Comic]({comic_data['img']})"
                    
            return "📚 Check out xkcd.com for amazing comics!"
                    
        except Exception as e:
            logger.error(f"Comic error: {e}")
            return "📚 Humor is the best medicine! 😄"

    async def get_random_activity(self) -> str:
        try:
            response = requests.get("https://www.boredapi.com/api/activity", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return f"🎮 *Activity Suggestion*\n\n*{data['activity']}*\n\nType: {data['type'].title()}\nParticipants: {data['participants']}"
            else:
                activities = [
                    "Read a book you've been meaning to read",
                    "Learn a new recipe and cook it",
                    "Call a friend or family member you haven't spoken to in a while",
                    "Go for a walk and observe your surroundings",
                    "Learn 5 words in a new language"
                ]
                return f"🎮 *Activity Suggestion*\n\n{random.choice(activities)}"
                    
        except Exception as e:
            logger.error(f"Activity error: {e}")
            return "🎮 How about learning something new today?"

    # Crypto Features
    async def get_crypto_prices(self) -> str:
        try:
            coins = ['bitcoin', 'ethereum', 'dogecoin', 'cardano', 'solana']
            prices_text = "₿ *Crypto Prices*\n\n"
            
            for coin in coins:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd&include_24hr_change=true"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if coin in data:
                        price = data[coin]['usd']
                        change = data[coin].get('usd_24h_change', 0)
                        change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                        prices_text += f"• {coin.title()}: ${price:,.2f} {change_emoji} {change:+.1f}%\n"
            
            prices_text += "\n_Data from CoinGecko_"
            return prices_text
            
        except Exception as e:
            logger.error(f"Crypto error: {e}")
            return "❌ Could not fetch crypto prices at the moment"

    async def get_specific_crypto(self, coin: str) -> str:
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd,eur,gbp&include_24hr_change=true&include_market_cap=true"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if coin in data:
                    crypto_data = data[coin]
                    price_usd = crypto_data['usd']
                    price_eur = crypto_data['eur']
                    price_gbp = crypto_data['gbp']
                    change = crypto_data.get('usd_24h_change', 0)
                    market_cap = crypto_data.get('usd_market_cap', 0)
                    
                    change_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
                    
                    return f"""₿ *{coin.title()} Price*

💵 USD: ${price_usd:,.2f}
💶 EUR: €{price_eur:,.2f}
💷 GBP: £{price_gbp:,.2f}

24h Change: {change_emoji} {change:+.1f}%
Market Cap: ${market_cap:,.0f}

_Data from CoinGecko_"""
            
            return f"❌ Could not fetch {coin} price"
            
        except Exception as e:
            logger.error(f"Crypto specific error: {e}")
            return f"❌ Error fetching {coin} price"

    # Weather Feature
    async def get_weather(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        location = update.message.text
        
        try:
            await update.message.reply_text(f"🌤️ Getting weather for {location}...")
            
            # First, get coordinates from location name
            geo_url = f"https://nominatim.openstreetmap.org/search?q={requests.utils.quote(location)}&format=json"
            geo_response = requests.get(geo_url, timeout=10)
            
            if geo_response.status_code == 200 and geo_response.json():
                geo_data = geo_response.json()[0]
                lat, lon = geo_data['lat'], geo_data['lon']
                display_name = geo_data['display_name']
                
                # Get weather data
                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto"
                weather_response = requests.get(weather_url, timeout=10)
                
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    current = weather_data['current_weather']
                    
                    temp = current['temperature']
                    windspeed = current['windspeed']
                    weather_code = current['weathercode']
                    
                    # Get daily forecast
                    daily = weather_data['daily']
                    today_max = daily['temperature_2m_max'][0]
                    today_min = daily['temperature_2m_min'][0]
                    
                    weather_desc = self.get_weather_description(weather_code)
                    
                    weather_text = f"""
🌤️ *Weather in {location}*

📍 {display_name.split(',')[0]}
🌡️ Current: {temp}°C
📊 Today: {today_min}°C - {today_max}°C
💨 Wind: {windspeed} km/h
☁️ Conditions: {weather_desc}

_Data from Open-Meteo_
                    """
                    
                    await update.message.reply_text(weather_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    await update.message.reply_text("❌ Could not fetch weather data for this location")
            else:
                await update.message.reply_text("❌ Location not found. Try a different city name.")
                
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
            82: "Violent rain showers",
            95: "Thunderstorm",
            96: "Thunderstorm with slight hail",
            99: "Thunderstorm with heavy hail"
        }
        return weather_codes.get(code, "Unknown conditions")

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
                
                await update.message.reply_text(f"💱 Converting {amount} {from_curr} to {to_curr}...")
                
                url = f"https://api.exchangerate.host/convert?from={from_curr}&to={to_curr}&amount={amount}"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['success']:
                        result = data['result']
                        rate = data['info']['rate']
                        date = data['date']
                        
                        conversion_text = f"""
💰 *Currency Conversion*

💵 {amount} {from_curr} = {result:.2f} {to_curr}
📊 Exchange Rate: 1 {from_curr} = {rate:.4f} {to_curr}
📅 Date: {date}

_Data from ExchangeRate.host_
                        """
                        
                        await update.message.reply_text(conversion_text, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await update.message.reply_text("❌ Currency conversion failed. Check currency codes.")
                else:
                    await update.message.reply_text("❌ Could not fetch exchange rates")
            else:
                await update.message.reply_text("❌ Invalid format. Use: '100 USD to KES'")
                
        except ValueError:
            await update.message.reply_text("❌ Invalid amount. Please enter a valid number.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error converting currency: {str(e)}")
        
        return ConversationHandler.END

    # AI Response Generator
    async def generate_ai_response(self, prompt: str) -> str:
        try:
            # Enhanced AI response using multiple approaches
            prompt_lower = prompt.lower()
            
            if any(word in prompt_lower for word in ['hello', 'hi', 'hey', 'hola']):
                return f"👋 Hello! I'm Advay Universe! How can I assist you today? Use the menu to explore my features! 🚀"
            elif any(word in prompt_lower for word in ['weather', 'temperature', 'forecast']):
                return "🌤️ Want weather info? Use the Utilities menu or click '🌤️ Weather' button!"
            elif any(word in prompt_lower for word in ['joke', 'funny', 'laugh']):
                joke = await self.get_random_joke()
                return joke
            elif any(word in prompt_lower for word in ['quote', 'inspiration', 'motivation']):
                quote = await self.get_random_quote()
                return quote
            elif any(word in prompt_lower for word in ['crypto', 'bitcoin', 'ethereum']):
                return "₿ Check crypto prices using the '📊 Crypto & Finance' menu!"
            elif any(word in prompt_lower for word in ['thank', 'thanks']):
                return "You're welcome! 😊 Let me know if you need anything else!"
            elif any(word in prompt_lower for word in ['how are you', 'how are you doing']):
                return "I'm doing great! Ready to help you with amazing features! 🤖"
            else:
                # Use pollinations.ai for general responses
                url = f"https://pollinations.ai/api/text?prompt={requests.utils.quote(prompt)}"
                response = requests.get(url, timeout=15)
                
                if response.status_code == 200:
                    return f"🤖 {response.text}\n\n_Powered by AI_"
                else:
                    return "I'm Advay Universe, your all-in-one assistant! 🌟 Use the menu buttons to explore my amazing features like AI image generation, crypto prices, weather, and much more! 🚀"
                    
        except Exception as e:
            return "I'm here to help! 🌟 Use the menu buttons to explore AI features, entertainment, utilities, and more! What would you like to try first? 😊"

    # Group welcome handler
    async def welcome_new_member(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        if update.message.new_chat_members:
            for member in update.message.new_chat_members:
                if member.id == context.bot.id:
                    # Bot was added to group
                    welcome_text = """
🤖 *Advay Universe has joined the group!*

I'm your multi-functional assistant! Here's what I can do in groups:

🎉 Entertainment: memes, jokes, quotes
💰 Utilities: weather, currency, crypto prices
🤖 AI: image generation, text completion
📊 Group: welcome messages, fun interactions

Use /help to see all commands!
                    """
                    await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN)
                else:
                    # Regular user joined
                    welcome_text = f"""
👋 Welcome {member.first_name} to the group!

I'm Advay Universe, your group assistant. 
Type /help to see what I can do! 🚀

Pro tip: Try /meme for some fun! 😄
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
        
        await update.message.reply_text("🔄 Starting broadcast... This may take a while.")
        
        for user_id in user_sessions.keys():
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📢 *Broadcast from Advay Universe Admin*\n\n{message}\n\n---\n_This is an automated broadcast_",
                    parse_mode=ParseMode.MARKDOWN
                )
                successful += 1
                await asyncio.sleep(0.1)  # Rate limiting
            except Exception as e:
                failed += 1
                logger.error(f"Broadcast failed for {user_id}: {e}")
        
        await update.message.reply_text(
            f"✅ *Broadcast Completed!*\n\n✅ Successful: {successful}\n❌ Failed: {failed}\n📊 Total Users: {len(user_sessions)}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        return ConversationHandler.END

    # Admin statistics
    async def admin_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Admin only feature")
            return
            
        total_users = len(user_sessions)
        now = datetime.now()
        active_today = sum(1 for user_data in user_sessions.values() 
                          if (now - user_data['last_active']).days < 1)
        active_week = sum(1 for user_data in user_sessions.values() 
                         if (now - user_data['last_active']).days < 7)
        
        total_usage = sum(user_data['usage_count'] for user_data in user_sessions.values())
        avg_usage = total_usage / total_users if total_users > 0 else 0
        
        stats_text = f"""
📊 *Bot Statistics*

👥 Total Users: {total_users}
🟢 Active Today: {active_today}
🟡 Active This Week: {active_week}
📈 Total Interactions: {total_usage}
📊 Avg. Usage per User: {avg_usage:.1f}

⏰ Last Updated: {now.strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN)

    # Cancel conversation
    async def cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        await update.message.reply_text("❌ Operation cancelled.")
        return ConversationHandler.END

    def setup_handlers(self, application: Application) -> None:
        # Basic commands
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CommandHandler("crypto", self.get_crypto_prices))
        application.add_handler(CommandHandler("meme", lambda u, c: asyncio.create_task(self.get_random_meme())))
        application.add_handler(CommandHandler("joke", lambda u, c: asyncio.create_task(self.get_random_joke())))
        application.add_handler(CommandHandler("quote", lambda u, c: asyncio.create_task(self.get_random_quote())))
        application.add_handler(CommandHandler("stats", self.admin_stats))
        
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
        
        conv_handler_qr = ConversationHandler(
            entry_points=[CallbackQueryHandler(self.button_handler, pattern="^generate_qr$")],
            states={
                QR_GENERATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.generate_qr_code)]
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
        
        application.add_handler(conv_handler_ai_image)
        application.add_handler(conv_handler_ai_text)
        application.add_handler(conv_handler_weather)
        application.add_handler(conv_handler_currency)
        application.add_handler(conv_handler_qr)
        application.add_handler(conv_handler_broadcast)

    async def post_init(self, application: Application) -> None:
        # Set bot commands
        commands = [
            BotCommand("start", "Start the bot"),
            BotCommand("help", "Show help"),
            BotCommand("meme", "Get random meme"),
            BotCommand("joke", "Get random joke"),
            BotCommand("quote", "Get inspirational quote"),
            BotCommand("crypto", "Crypto prices"),
            BotCommand("weather", "Get weather info"),
            BotCommand("stats", "Admin statistics"),
        ]
        await application.bot.set_my_commands(commands)

    def run(self):
        """Run the bot"""
        application = Application.builder().token(BOT_TOKEN).post_init(self.post_init).build()
        self.application = application
        
        self.setup_handlers(application)
        
        logger.info("🤖 Advay Universe Bot is starting...")
        logger.info(f"👤 Admin ID: {ADMIN_ID}")
        logger.info(f"👥 Pre-loaded users: {len(user_sessions)}")
        
        application.run_polling()

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable is required!")
        return
    
    bot = AdvayUniverseBot()
    bot.run()

if __name__ == "__main__":
    main()
