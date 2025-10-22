import requests
import json
import time
import os
import socketserver
import threading
import random
import asyncio
import pytz
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from collections import defaultdict
import uuid
import html
from flask import Flask
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for health checks
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>SYAPA BOT</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    text-align: center; 
                    padding: 50px; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    background: rgba(255,255,255,0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                .status { 
                    color: #00ff00; 
                    font-size: 28px; 
                    font-weight: bold;
                }
                .info { 
                    margin: 20px 0; 
                    font-size: 18px;
                }
                .owner {
                    color: #ffcc00;
                    font-weight: bold;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="status">🟢 SYAPA BOT IS RUNNING!</h1>
                <div class="info">
                    <p><strong>Owner:</strong> <span class="owner">👿 SYAPA KING 👿</span></p>
                    <p><strong>Active Users:</strong> {}</p>
                    <p><strong>Server Time:</strong> {}</p>
                    <p><strong>Status:</strong> ✅ Online & Monitoring</p>
                </div>
                <p>
                    <a href="/health" style="color: #00ff00; margin: 0 10px;">Health Check</a> | 
                    <a href="/status" style="color: #00ff00; margin: 0 10px;">Status</a>
                </p>
            </div>
        </body>
    </html>
    """.format(len(active_tasks), datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %I:%M:%S %p"))

@app.route('/health')
def health():
    return "OK", 200

@app.route('/status')
def status():
    return {
        "status": "running",
        "bot": "online",
        "active_users": len(active_tasks),
        "timestamp": datetime.now().isoformat(),
        "server": "Koyeb",
        "owner": "SYAPA KING"
    }

def run_flask():
    port = int(os.environ.get('PORT', 8000))
    logger.info(f"🚀 Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

# Telegram bot token from environment variable
TELEGRAM_BOT_TOKEN = os.environ.get('BOT_TOKEN', '7791213862:AAFvGyuCCVZqpnQQwjZBbu89drzuiJPAcJM')

# Dictionary to track active SMS sending tasks for each user
active_tasks = {}

# List of approved keys - you can add more keys here
APPROVED_KEYS = ['syapahere', 'syapaking', 'syapa83', 'syapa64', '𝐜𝐚𝐭𝐨']

# Your Facebook contact
FACEBOOK_CONTACT = 'https://www.facebook.com/share/168AJz6Ehm/'

# Dictionary to track user approval status
user_approval_status = {}

# Dictionary to track user statistics
user_stats = defaultdict(lambda: {
    'messages_sent': 0,
    'last_activity': None,
    'running': False
})

class MyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = self.request.recv(1024).strip()
        self.request.sendall(b"TRICKS BY SYAPA")

def run_server():
    PORT = int(os.environ.get('PORT', 4000))
    server = socketserver.ThreadingTCPServer(("0.0.0.0", PORT), MyHandler)
    logger.info(f"🔧 Server running on port {PORT}")
    server.serve_forever()

def validate_token(token):
    try:
        response = requests.get(f"https://graph.facebook.com/v20.0/me?access_token={token}", timeout=10)
        data = response.json()
        return 'id' in data  # True if token is valid
    except Exception as e:
        logger.error(f"Token validation error: {str(e)}")
        return False

def fetch_groups(token):
    try:
        # Get conversations with names in a single request
        response = requests.get(
            f"https://graph.facebook.com/v20.0/me/conversations?fields=name,id&access_token={token}&limit=100",
            timeout=10
        )
        data = response.json()
        
        if 'error' in data:
            logger.error(f"Facebook API error: {data['error']['message']}")
            return []
        
        # Handle pagination if needed
        conversations = data.get('data', [])
        while 'paging' in data and 'next' in data['paging']:
            try:
                response = requests.get(data['paging']['next'], timeout=10)
                data = response.json()
                if 'error' in data:
                    logger.error(f"Facebook API pagination error: {data['error']['message']}")
                    break
                conversations.extend(data.get('data', []))
            except Exception as e:
                logger.error(f"Error during pagination: {str(e)}")
                break
        
        return conversations
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error fetching groups: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error fetching groups: {str(e)}")
        return []

async def send_messages_from_file(token, tid, hater_name, speed, file_content, chat_id, context, user_id):
    message_count = 0
    headers = {"Content-Type": "application/json"}

    # Update user stats
    user_stats[user_id]['running'] = True
    user_stats[user_id]['last_activity'] = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %I:%M:%S %p")

    messages = [msg.strip() for msg in file_content.split('\n') if msg.strip()]

    try:
        while not context.user_data.get('stop_sending', False):
            for message in messages:
                # Check stop flag again between each message
                if context.user_data.get('stop_sending', False):
                    break

                # If this user's task has been canceled, exit
                if user_id not in active_tasks:
                    return {"status": "canceled", "messages_sent": message_count}

                url = f"https://graph.facebook.com/v20.0/{'t_' + tid}/"
                full_message = hater_name + ' ' + message
                parameters = {'access_token': token, 'message': full_message}

                try:
                    response = requests.post(url, json=parameters, headers=headers, timeout=10)
                    message_count += 1
                    current_time = time.strftime("%Y-%m-%d %I:%M:%S %p")

                    status_message = ""
                    if response.status_code == 200:
                        status_message = f"✅ SMS SENT! {message_count} to Convo {tid}: {html.escape(full_message)}"
                        logger.info(f"✅ CHALA GEYA SMS {message_count} of Convo {tid}")
                        # Update user stats when message is sent successfully
                        user_stats[user_id]['messages_sent'] += 1
                    else:
                        status_message = f"❌ SMS FAILED! {message_count} to Convo {tid}: {html.escape(full_message)}"
                        logger.error(f"❌ MSG NAHI JA RAHA HAI {message_count} of Convo {tid}")

                    # Send real-time update to Telegram
                    if chat_id:
                        await context.bot.send_message(chat_id=chat_id, text=status_message)
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
                    if chat_id:
                        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Error sending message: {str(e)}")

                # Wait for specified speed between messages
                try:
                    speed_seconds = float(speed)
                    await asyncio.sleep(speed_seconds)
                except ValueError:
                    await asyncio.sleep(1)  # Default to 1 second if speed is invalid

        await context.bot.send_message(chat_id=chat_id, text=f"🛑 Stopped SMS sending after {message_count} messages.")
    except Exception as e:
        logger.error(f"Error in send_messages: {str(e)}")
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Error in SMS loop: {str(e)}")
    finally:
        # Update user stats
        user_stats[user_id]['running'] = False
        user_stats[user_id]['last_activity'] = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %I:%M:%S %p")

        # Clean up active task reference
        if user_id in active_tasks:
            del active_tasks[user_id]
        return {"status": "completed", "messages_sent": message_count}

async def generate_unique_key(user_id):
    existing_key = await get_user_key(user_id)
    if existing_key:
        return existing_key

    unique_key = f"syapa_{uuid.uuid4().hex[:8]}"

    all_keys = await get_all_keys()
    while unique_key in all_keys:
        unique_key = f"syapa_{uuid.uuid4().hex[:8]}"

    with open('users.txt', 'a') as f:
        f.write(f"{user_id}:{unique_key}\n")
    
    return unique_key

async def get_user_key(user_id):
    try:
        with open('users.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        uid, key = line.split(':')
                        if str(user_id) == uid:
                            return key.strip()
                    except ValueError:
                        continue
    except FileNotFoundError:
        with open('users.txt', 'w') as f:
            f.write("# User ID : Key mapping\n# Format: user_id:key\n")
    return None

async def get_all_keys():
    keys = set()
    try:
        with open('users.txt', 'r') as f:
            lines = f.readlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        _, key = line.split(':')
                        keys.add(key.strip())
                    except ValueError:
                        continue
    except FileNotFoundError:
        pass
    return keys

async def is_key_approved(key):
    if key in APPROVED_KEYS:
        return True

    try:
        with open('approved.txt', 'r') as f:
            lines = f.readlines()
            approved_keys = [line.strip() for line in lines if line.strip() and not line.startswith('#')]
            return key in approved_keys
    except FileNotFoundError:
        with open('approved.txt', 'w') as f:
            f.write("# Approved keys\n# One key per line\n")

    return False

async def approve_key(key):
    if not await is_key_approved(key):
        with open('approved.txt', 'a') as f:
            f.write(f"{key}\n")
        return True
    return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username or "User"

    context.user_data.clear()

    user_key = await generate_unique_key(user_id)

    if not await get_user_key(user_id):
        with open('users.txt', 'a') as f:
            f.write(f"{user_id}:{user_key}\n")
        welcome_message = f"""
𝑾𝑬𝑳𝑳𝑪𝑶𝑴𝑬 𝑻𝑶 𝑻𝑯𝑬 𝑺𝒀𝑨𝑷𝑨 𝑩𝑶𝑻! ✨
🔹 𝐵𝑜𝑡 𝑘𝑜 𝑢𝑠𝑒 𝑘𝑟𝑛𝑦 𝑘𝑦 𝑙𝑖𝑦𝑒 𝑎𝑝𝑝𝑟𝑜𝑣𝑒𝑙 𝑙𝑜 𝑚𝑒𝑟𝑦 𝐵𝑜𝑠𝑠 𝑆𝑦𝑎𝑝𝑎 𝑠𝑒.
🔹 𝐴𝑝𝑝𝑟𝑜𝑣𝑒𝑙 𝑘𝑒𝑦 𝑚𝑒𝑟𝑦 𝐵𝑜𝑠𝑠 𝑠𝑦𝑎𝑝𝑎 𝑘𝑦 𝑖𝑛𝑏𝑜𝑥 𝑠𝑒𝑛𝑑 𝑘𝑟𝑜 !

𝑇𝑢𝑚ℎ𝑎𝑟𝑖 𝐴𝑝𝑝𝑟𝑜𝑣𝑒𝑙 𝐾𝑒𝑦: `{user_key}`
𝑆𝑡𝑎𝑡𝑢𝑠: 🟡 𝑃𝑒𝑛𝑑𝑖𝑛𝑔

🔹 𝑇ℎ𝑜𝑟𝑎 𝑖𝑛𝑡𝑖𝑧𝑎𝑟 𝑘𝑟𝑜 𝐴𝑝𝑝𝑟𝑜𝑣𝑒𝑙.
🔹 𝑌𝑒 𝑚𝑒𝑟𝑦 𝑏𝑜𝑠𝑠 𝑠𝑦𝑎𝑝𝑎 𝑘𝑖 𝐹𝑎𝑐𝑒𝑏𝑜𝑜𝑘 : {FACEBOOK_CONTACT}

°°_________________________••
𝑶𝑾𝑵𝑬𝑹: 😈𝑺𝒀𝑨𝑷𝑨 𝑲𝑰𝑵𝑮
°°_________________________°°
"""
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
        context.user_data['step'] = 'waiting_for_approval'
        return

    if await is_key_approved(user_key):
        await update.message.reply_text('You are approved ✅ Please send your Facebook token.')
        context.user_data['step'] = 'waiting_for_token'
    else:
        vip_message = f"""
━━━━━━━━━━━━━━━━━━
🔥 𝑽𝑰𝑷 𝑨𝑪𝑪𝑬𝑺𝑺 𝑹𝑬𝑸𝑼𝑰𝑹𝑬𝑫! 🔥
━━━━━━━━━━━━━━━━━━

🚫 𝑨𝑪𝑪𝑬𝑺𝑿 𝑫𝑬𝑵𝑰𝑬𝑫! 🚫

🔑 Your VIP Key: (`{user_key}`)
⚠️ Status: ❌ 𝐍𝐨𝐭 𝐀𝐩𝐩𝐫𝑜𝑣𝑒𝑑 ❌

📌 𝑷𝒍𝒆𝒂𝒔𝒆 𝑪𝒐𝒏𝒕𝒂𝒄𝒕 𝑻𝒉𝒆 𝑶𝒘𝒏𝑬𝑹 𝑭𝒐𝒓 𝑨𝒑𝒑𝐫𝑜𝑣𝒂𝒍!

📲 Facebook: {FACEBOOK_CONTACT}

🔰 𝑷𝒓𝒆𝒎𝒊𝒖𝒎 𝑼𝒔𝒆𝒓𝒔 𝑶𝒏𝒍𝒚! 🔰

━━━━━━━━━━━━━━━━━━
👑 𝑶𝑾𝑵𝑬𝑹:  𝑺𝒀𝑨𝑷𝑨 𝑲𝑰𝑵𝑮👑
━━━━━━━━━━━━━━━━━━"""
        await update.message.reply_text(vip_message, parse_mode='Markdown')
        context.user_data['step'] = 'waiting_for_approval'

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
*Available Commands:*

/start - Start the bot and get your approval key
/help - Show this help message
/status - Check your approval status
/stop - Stop the SMS sending process (Approved users only)

*For Approved Users:*
- Send Facebook token to start sending messages
- Configure speed and message settings
- Monitor message delivery status
Send me your token, TID, speed, hater name, and message file to send SMS.

Commands:
/start - Start the bot
/help - Show this help message
/stop - Stop the SMS sending process
/status - Check your stats and active users

For approval or support, contact on Facebook:
📱 """ + FACEBOOK_CONTACT + """

The bot will continuously send messages in a loop until you send the /stop command.
"""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    user_key = await get_user_key(user_id)
    if not user_key or not await is_key_approved(user_key):
        await update.message.reply_text("You need to be approved to use this service. Use /start to begin the approval process.")
        return

    context.user_data['stop_sending'] = True

    if 'token' in context.user_data:
        stored_token = context.user_data['token']
        context.user_data.clear()
        context.user_data['token'] = stored_token
        context.user_data['stop_sending'] = True

    if user_id in active_tasks:
        await update.message.reply_text('🛑 Stopping your SMS sending process. Please wait...')
        del active_tasks[user_id]
    else:
        await update.message.reply_text('ℹ️ You don\'t have any active SMS sending process.')

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_key = await get_user_key(user_id)

    if not user_key:
        await update.message.reply_text("⚠️ You haven't started the bot yet. Use /start to begin.")
        return

    is_approved = await is_key_approved(user_key)
    status_emoji = "✅" if is_approved else "🟡"
    status_text = "Approved" if is_approved else "Pending"

    status_message = f"""
*Bot Status Report* 📊

*Your Status:*
Key: `{user_key}`
Status: {status_emoji} {status_text}
"""

    if is_approved:
        active_users = sum(1 for uid, stats in user_stats.items() if stats['running'])
        user_messages = user_stats[user_id]['messages_sent']
        last_activity = user_stats[user_id]['last_activity'] or "Never"

        status_message += f"""
*Your Stats:*
Messages Sent: {user_messages}
Last Activity: {last_activity}

*System Stats:*
Active Users: {active_users}/50
"""

    status_message += f"""
*Support:*
Facebook: {FACEBOOK_CONTACT}
Owner: *👿𝐒𝐘𝐀𝐏𝐀 𝐊𝐈𝐍𝐆👿*
    """

    await update.message.reply_text(status_message, parse_mode='Markdown')

async def add_key(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if not update.message.text.startswith('/addkey '):
        await update.message.reply_text('Usage: /addkey <new_key>')
        return

    new_key = update.message.text.split(' ', 1)[1].strip()

    if new_key in APPROVED_KEYS:
        await update.message.reply_text(f'The key \'{new_key}\' already exists!')
        return

    APPROVED_KEYS.append(new_key)
    await update.message.reply_text(f'Key \'{new_key}\' added successfully!')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    if 'step' in context.user_data and context.user_data['step'] == 'waiting_for_approval':
        approval_key = update.message.text.strip()

        if not await get_user_key(user_id):
            with open('users.txt', 'a') as f:
                f.write(f"{user_id}:{approval_key}\n")

        if await is_key_approved(approval_key):
            stored_token = context.user_data.get('token', None)
            context.user_data.clear()
            if stored_token:
                context.user_data['token'] = stored_token

            await update.message.reply_text('✅ Your key has been approved! You can now use the bot.')
            await update.message.reply_text('Please send your token.')
            context.user_data['step'] = 'waiting_for_token'
        else:
            await update.message.reply_text('❌ Invalid approval key. Please contact the admin on Facebook:')
            await update.message.reply_text(f'📱 {FACEBOOK_CONTACT}')
        return

    user_key = await get_user_key(user_id)
    if not user_key or not await is_key_approved(user_key):
        await update.message.reply_text("You need to be approved to use this service. Use /start to begin the approval process.")
        return

    if 'step' not in context.user_data:
        context.user_data['step'] = 'waiting_for_token'

    if context.user_data['step'] == 'waiting_for_token':
        token = update.message.text.strip()
        if not validate_token(token):
            await update.message.reply_text("⚠️ Invalid token. Please check and try again.")
            return
        groups = fetch_groups(token)
        context.user_data['token'] = token

        group_list = "💫 Available Groups/Conversations 💫\n\n"
        for i, group in enumerate(groups, 1):
            group_name = html.escape(group.get('name', 'Unnamed Conversation'))
            group_id = group.get('id', 'N/A')
            group_list += f"{i}. {group_name}\nUID/TID: <code>{group_id}</code>\n\n"
        
        # Split the message if too long
        max_length = 4096  # Telegram message limit
        if len(group_list) > max_length:
            parts = [group_list[i:i+max_length] for i in range(0, len(group_list), max_length)]
            for part in parts:
                await update.message.reply_text(part, parse_mode='HTML')
        else:
            await update.message.reply_text(group_list, parse_mode='HTML')
            
        await update.message.reply_text('Please send the TID you want to use from the list above.')
        context.user_data['step'] = 'waiting_for_tid'

    elif context.user_data['step'] == 'waiting_for_tid':
        context.user_data['tid'] = update.message.text
        await update.message.reply_text('TID received. Now please send the speed (in seconds between messages).')
        context.user_data['step'] = 'waiting_for_speed'

    elif context.user_data['step'] == 'waiting_for_speed':
        context.user_data['speed'] = update.message.text
        await update.message.reply_text('Speed received. Now please send the hater\'s name.')
        context.user_data['step'] = 'waiting_for_hater_name'

    elif context.user_data['step'] == 'waiting_for_hater_name':
        context.user_data['hater_name'] = update.message.text
        await update.message.reply_text('Hater name received. Now please send the text file or paste your messages.')
        context.user_data['step'] = 'waiting_for_file_content'

    elif context.user_data['step'] == 'waiting_for_file_content':
        context.user_data['file_content'] = update.message.text
        username = update.effective_user.username or "User"
        current_time = datetime.now(pytz.timezone('Asia/Karachi')).strftime("%Y-%m-%d %I:%M:%S %p")

        start_message = f"""
*SMS Sending Started* ✅
*User:* {username}
*Time:* {current_time}
*TID:* {context.user_data['tid']}
*Speed:* {context.user_data['speed']} seconds

This will continue looping until you send /stop command.
For any issues, contact on Facebook: {FACEBOOK_CONTACT}
        """

        await update.message.reply_text(start_message, parse_mode='Markdown')

        context.user_data['stop_sending'] = False

        user_id = update.effective_user.id

        if user_id in active_tasks:
            context.user_data['stop_sending'] = True
            await asyncio.sleep(0.5)

        chat_id = update.effective_chat.id
        sms_task = asyncio.create_task(
            send_messages_from_file(
                context.user_data['token'],
                context.user_data['tid'],
                context.user_data['hater_name'],
                context.user_data['speed'],
                context.user_data['file_content'],
                chat_id,
                context,
                user_id
            )
        )

        active_tasks[user_id] = sms_task

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id

    user_key = await get_user_key(user_id)
    if not user_key or not await is_key_approved(user_key):
        await update.message.reply_text("You need to be approved to use this service. Use /start to begin the approval process.")
        return

    if 'step' not in context.user_data or context.user_data['step'] != 'waiting_for_file_content':
        await update.message.reply_text('Please first send token, TID, speed, and hater name.')
        return

    file = await update.message.document.get_file()

    file_content = ""
    try:
        file_bytes = await file.download_as_bytearray()
        file_content = file_bytes.decode('utf-8')
    except Exception as e:
        await update.message.reply_text(f'Error reading file: {str(e)}')
        return

    await update.message.reply_text('File received. Starting to send SMS. This will continue looping until you send /stop command.')

    context.user_data['stop_sending'] = False

    user_id = update.effective_user.id

    if user_id in active_tasks:
        context.user_data['stop_sending'] = True
        await asyncio.sleep(0.5)

    chat_id = update.effective_chat.id
    sms_task = asyncio.create_task(
        send_messages_from_file(
            context.user_data['token'],
            context.user_data['tid'],
            context.user_data['hater_name'],
            context.user_data['speed'],
            file_content,
            chat_id,
            context,
            user_id
        )
    )

    active_tasks[user_id] = sms_task

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Update caused error: {context.error}")
    if isinstance(update, Update) and update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"⚠️ An error occurred: {str(context.error)}"
        )

def main() -> None:
    logger.info("🚀 Starting Syapa Bot...")
    
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("✅ Flask health server started")

    # Start your existing server
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    logger.info("✅ Main server started")

    # Start Telegram bot
    builder = Application.builder()
    application = builder.token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("addkey", add_key))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    application.add_error_handler(error_handler)

    logger.info("🤖 Telegram Bot started successfully!")
    logger.info("📊 Health check available at: http://0.0.0.0:8000/health")
    logger.info("👑 Owner: SYAPA KING")
    logger.info("🔧 Bot is now running and monitoring...")

    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        pool_timeout=30,
        read_timeout=30,
        write_timeout=30,
        connect_timeout=30
    )

if __name__ == "__main__":
    main()
