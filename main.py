import discord
from discord.ext import commands
from flask import Flask, jsonify
import threading
import os
import datetime
import logging
import sys
import asyncio

# ====== LOGGING SETUP ======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Suppress discord.py debug logs
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.http').setLevel(logging.WARNING)

# ====== WEB KEEP-ALIVE ======
app = Flask(__name__)

bot_status = {
    "running": False,
    "connected": False,
    "messages_forwarded": 0,
    "errors": 0,
    "last_message_time": None,
    "last_error": None,
    "uptime_start": datetime.datetime.now()
}

@app.route('/')
def home():
    uptime = datetime.datetime.now() - bot_status["uptime_start"]
    return jsonify({
        "status": "alive",
        "bot_running": bot_status["running"],
        "connected": bot_status["connected"],
        "messages_forwarded": bot_status["messages_forwarded"],
        "errors": bot_status["errors"],
        "last_message": bot_status["last_message_time"],
        "uptime_seconds": int(uptime.total_seconds()),
        "last_error": bot_status["last_error"]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy" if bot_status["connected"] else "disconnected",
        "timestamp": datetime.datetime.now().isoformat()
    })

def run_web():
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"🌐 Starting Flask web server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ====== CONFIGURATION ======
# Get token from environment variable (IMPORTANT!)
USER_TOKEN = os.environ.get("DISCORD_USER_TOKEN", "").strip()

# Fallback to hardcoded if env var not set (NOT RECOMMENDED for production)
if not USER_TOKEN:
    logger.warning("⚠️ DISCORD_USER_TOKEN not found in environment, using fallback")
    USER_TOKEN = "MTQzNDk3MjEwNzAzMjM2NzMzNw.G5_xrs.y5BkXtKacHhL0jI3Kn6dLgKcO2kyuVUzpwD4Nk"

SOURCE_CHANNEL_ID = int(os.environ.get("SOURCE_CHANNEL_ID", "1376365659830616207"))
DEST_CHANNEL_ID = int(os.environ.get("DEST_CHANNEL_ID", "1435185554730782750"))

# Validate token
if not USER_TOKEN:
    logger.error("❌ DISCORD_USER_TOKEN environment variable not set!")
    logger.error("Please set your Discord user token in environment variables")
    sys.exit(1)

# ====== DISCORD CLIENT SETUP ======
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.dm_messages = True  # Added for DM support

client = discord.Client(intents=intents)

# ====== HEALTH CHECK TASK ======
async def periodic_health_check():
    """Periodic health check to prevent getting stuck"""
    await client.wait_until_ready()
    while not client.is_closed():
        try:
            await asyncio.sleep(30)  # Check every 30 seconds
            if client.is_ready():
                bot_status["connected"] = True
            else:
                bot_status["connected"] = False
                logger.warning("⚠️ Bot not ready, connection may be stuck")
        except Exception as e:
            logger.error(f"Health check error: {e}")

# ====== EVENT HANDLERS ======

@client.event
async def on_ready():
    """Called when bot successfully connects"""
    bot_status["running"] = True
    bot_status["connected"] = True
    
    logger.info("=" * 70)
    logger.info(f"✅ Logged in as: {client.user.name} ({client.user.id})")
    logger.info(f"📤 Source Channel ID: {SOURCE_CHANNEL_ID}")
    logger.info(f"📥 Destination Channel ID: {DEST_CHANNEL_ID}")
    logger.info("=" * 70)
    
    # Start health check task
    client.loop.create_task(periodic_health_check())
    
    # Verify channels exist with retry
    max_retries = 3
    for attempt in range(max_retries):
        try:
            source_channel = client.get_channel(SOURCE_CHANNEL_ID)
            dest_channel = client.get_channel(DEST_CHANNEL_ID)
            
            if not source_channel:
                logger.warning(f"⏳ Attempt {attempt+1}/{max_retries}: Fetching source channel...")
                try:
                    source_channel = await client.fetch_channel(SOURCE_CHANNEL_ID)
                except:
                    pass
            
            if not dest_channel:
                logger.warning(f"⏳ Attempt {attempt+1}/{max_retries}: Fetching destination channel...")
                try:
                    dest_channel = await client.fetch_channel(DEST_CHANNEL_ID)
                except:
                    pass
            
            if source_channel and dest_channel:
                break
                
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"Error fetching channels: {e}")
    
    if not source_channel:
        logger.error(f"❌ Cannot access source channel: {SOURCE_CHANNEL_ID}")
        logger.error("Make sure you have access to this channel!")
        bot_status["last_error"] = "Cannot access source channel"
    else:
        logger.info(f"✅ Source channel found: #{source_channel.name if hasattr(source_channel, 'name') else 'DM'}")
    
    if not dest_channel:
        logger.error(f"❌ Cannot access destination channel: {DEST_CHANNEL_ID}")
        logger.error("Make sure you have access to this channel!")
        bot_status["last_error"] = "Cannot access destination channel"
    else:
        logger.info(f"✅ Destination channel found: #{dest_channel.name if hasattr(dest_channel, 'name') else 'DM'}")
    
    if source_channel and dest_channel:
        logger.info("👀 Now monitoring for messages...")
        bot_status["last_error"] = None
    else:
        logger.error("⚠️ Bot is running but cannot access one or both channels")

@client.event
async def on_message(message):
    """Called when any message is received"""
    try:
        # Ignore our own messages
        if message.author.id == client.user.id:
            return
        
        # Check if message is from source channel
        if message.channel.id != SOURCE_CHANNEL_ID:
            return
        
        logger.info(f"📨 New message in source channel from {message.author.name}")
        logger.info(f"Content: {message.content[:100]}{'...' if len(message.content) > 100 else ''}")
        
        # Get destination channel
        dest_channel = client.get_channel(DEST_CHANNEL_ID)
        
        if not dest_channel:
            logger.warning("Destination channel not in cache, fetching...")
            try:
                dest_channel = await client.fetch_channel(DEST_CHANNEL_ID)
            except Exception as e:
                logger.error(f"❌ Cannot fetch destination channel: {e}")
                bot_status["errors"] += 1
                bot_status["last_error"] = f"Cannot access destination: {e}"
                return
        
        # Prepare message content
        content = message.content
        
        # Handle attachments (images, files, etc.)
        if message.attachments:
            attachment_urls = [att.url for att in message.attachments]
            content += "\n" + "\n".join(attachment_urls)
            logger.info(f"📎 Forwarding {len(message.attachments)} attachment(s)")
        
        # Handle embeds (rich content)
        embeds_to_forward = []
        if message.embeds:
            logger.info(f"📊 Forwarding {len(message.embeds)} embed(s)")
            embeds_to_forward = message.embeds[:10]  # Discord limit
        
        # Send to destination
        if content or embeds_to_forward:
            try:
                await dest_channel.send(content=content if content else None, embeds=embeds_to_forward)
                
                bot_status["messages_forwarded"] += 1
                bot_status["last_message_time"] = datetime.datetime.now().isoformat()
                
                logger.info(f"✅ Message forwarded successfully! (Total: {bot_status['messages_forwarded']})")
                
            except discord.errors.Forbidden:
                logger.error("❌ No permission to send messages in destination channel")
                bot_status["errors"] += 1
                bot_status["last_error"] = "Permission denied in destination"
            except discord.errors.HTTPException as e:
                logger.error(f"❌ Failed to send message: {e}")
                bot_status["errors"] += 1
                bot_status["last_error"] = str(e)
        else:
            logger.warning("⚠️ Message has no content or embeds to forward")
            
    except Exception as e:
        logger.error(f"💥 Error processing message: {e}", exc_info=True)
        bot_status["errors"] += 1
        bot_status["last_error"] = str(e)

@client.event
async def on_error(event, *args, **kwargs):
    """Called when an error occurs"""
    logger.error(f"💥 Discord error in {event}", exc_info=True)
    bot_status["errors"] += 1

@client.event
async def on_disconnect():
    """Called when bot disconnects"""
    logger.warning("⚠️ Disconnected from Discord")
    bot_status["connected"] = False

@client.event
async def on_resumed():
    """Called when connection is resumed"""
    logger.info("✅ Reconnected to Discord")
    bot_status["connected"] = True

# ====== MAIN ======

def main():
    """Main entry point"""
    logger.info("=" * 70)
    logger.info("🤖 Discord Self-Bot Message Forwarder")
    logger.info(f"📅 Started: {datetime.datetime.now()}")
    logger.info("⚠️  WARNING: Self-bots violate Discord ToS")
    logger.info("=" * 70)
    
    # Start web server in background
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    logger.info("✅ Web server thread started")
    
    # Give web server time to start
    import time
    time.sleep(2)
    
    try:
        # Run the Discord client
        logger.info("🔌 Connecting to Discord...")
        logger.info(f"Token starts with: {USER_TOKEN[:20]}...")
        
        # For user accounts (self-bots), just pass the token directly
        client.run(USER_TOKEN, reconnect=True)
        
    except discord.errors.LoginFailure as e:
        logger.error(f"❌ Invalid Discord token! Error: {e}")
        logger.error("Your token may be expired or invalid")
        logger.error("Please check your DISCORD_USER_TOKEN environment variable")
        bot_status["last_error"] = "Invalid token"
        
        # Keep web server alive to show error status
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("👋 Shutting down gracefully...")
        bot_status["running"] = False
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        bot_status["last_error"] = str(e)
        
        # Keep web server alive
        while True:
            time.sleep(60)

if __name__ == "__main__":
    main()
