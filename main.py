from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from flask import Flask, jsonify, request
import threading
import os
import time
import random
import datetime
import logging
import sys

# ====== LOGGING SETUP ======
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ====== WEB KEEP-ALIVE ======
app = Flask(__name__)

bot_status = {
    "running": False,
    "last_check": None,
    "messages_forwarded": 0,
    "errors": 0,
    "last_error": None,
    "uptime_start": datetime.datetime.now()
}

@app.route('/')
def home():
    uptime = datetime.datetime.now() - bot_status["uptime_start"]
    return jsonify({
        "status": "alive",
        "bot_running": bot_status["running"],
        "messages_forwarded": bot_status["messages_forwarded"],
        "errors": bot_status["errors"],
        "last_check": bot_status["last_check"],
        "uptime_seconds": uptime.total_seconds(),
        "last_error": bot_status["last_error"]
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.route('/restart', methods=['POST'])
def restart():
    logger.info("Manual restart requested via API")
    return jsonify({"status": "restart_not_implemented", "message": "Please redeploy on Render"})

def run_web():
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Starting Flask web server on port {port}")
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Start web server in background
web_thread = threading.Thread(target=run_web, daemon=True)
web_thread.start()
logger.info("Web server thread started")

# ====== CONFIGURATION ======
DISCORD_URL = "https://discord.com/login"
LOGIN_EMAIL = os.environ.get("DISCORD_EMAIL", "solostudy110012@gmail.com")
LOGIN_PASSWORD = os.environ.get("DISCORD_PASSWORD", "JESUSBPS123@")
SOURCE_CHANNEL_ID = os.environ.get("SOURCE_CHANNEL", "1376365659830616207")
DESTINATION_CHANNEL_ID = os.environ.get("DEST_CHANNEL", "1435185554730782750")

# Timing configuration
CHECK_INTERVAL = 8  # seconds between checks
RESTART_DELAY = 30  # seconds before restart after failure
MAX_CONSECUTIVE_FAILURES = 5
SESSION_REFRESH_INTERVAL = 3600  # refresh session every hour

class SessionKeeper:
    def __init__(self):
        self.last_activity = time.time()
        self.consecutive_failures = 0
        self.last_success = time.time()
        self.session_start = time.time()
        
    def update_activity(self):
        self.last_activity = time.time()
        
    def record_success(self):
        self.consecutive_failures = 0
        self.last_success = time.time()
        
    def record_failure(self):
        self.consecutive_failures += 1
        bot_status["errors"] += 1
        
    def needs_restart(self):
        return self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES
    
    def needs_refresh(self):
        # Refresh session every hour to prevent staleness
        return (time.time() - self.session_start) > SESSION_REFRESH_INTERVAL

def create_render_driver():
    """Create Chrome driver optimized for Render with anti-detection"""
    options = Options()
    
    # Essential Render configuration
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--headless=new")
    options.add_argument("--disable-setuid-sandbox")
    
    # Window and performance
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-logging")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    
    # Memory optimization for Render
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-backgrounding-occluded-windows")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-features=TranslateUI")
    
    # Anti-detection (Critical for Discord)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Realistic user agent
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    
    # Language and timezone
    options.add_argument("--lang=en-US")
    options.add_experimental_option("prefs", {
        "intl.accept_languages": "en-US,en",
        "profile.default_content_setting_values.notifications": 2
    })
    
    try:
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        # Enhanced stealth modifications
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
                window.chrome = {runtime: {}};
            """
        })
        
        logger.info("✅ Chrome driver created successfully")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Failed to create Chrome driver: {e}")
        bot_status["last_error"] = str(e)
        return None

def human_delay(min_sec=0.3, max_sec=0.8):
    """More human-like delays"""
    time.sleep(random.uniform(min_sec, max_sec))

def type_like_human(element, text, clear_first=True):
    """Type text with human-like patterns"""
    try:
        if clear_first:
            element.clear()
            human_delay(0.2, 0.5)
        
        # Random typing speed variation
        for char in text:
            element.send_keys(char)
            # Occasional longer pauses (thinking)
            if random.random() < 0.1:
                time.sleep(random.uniform(0.1, 0.3))
            else:
                time.sleep(random.uniform(0.05, 0.15))
        
        return True
    except Exception as e:
        logger.error(f"Error typing: {e}")
        return False

def robust_login(driver):
    """Enhanced login with better error handling"""
    try:
        logger.info("🔐 Starting login process...")
        driver.get(DISCORD_URL)
        human_delay(4, 6)
        
        wait = WebDriverWait(driver, 30)
        
        # Wait for page load
        try:
            email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
            logger.info("Email field found")
        except TimeoutException:
            logger.error("Email field not found - page may not have loaded")
            return False
        
        # Enter email
        human_delay(1, 2)
        if not type_like_human(email_field, LOGIN_EMAIL):
            return False
        
        human_delay(1, 2)
        
        # Enter password
        try:
            password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            logger.info("Password field found")
        except TimeoutException:
            logger.error("Password field not found")
            return False
        
        if not type_like_human(password_field, LOGIN_PASSWORD):
            return False
        
        human_delay(1, 2)
        
        # Submit
        password_field.send_keys(Keys.RETURN)
        logger.info("📤 Login form submitted")
        
        # Wait for redirect with extended timeout
        time.sleep(15)
        
        # Check for successful login
        current_url = driver.current_url
        logger.info(f"Current URL after login: {current_url}")
        
        if "channels" in current_url or ("login" not in current_url and "discord.com" in current_url):
            logger.info("✅ Login successful")
            return True
        else:
            logger.warning(f"⚠️ Login uncertain - URL: {current_url}")
            # Try to proceed anyway
            return True
            
    except Exception as e:
        logger.error(f"❌ Login failed with exception: {e}")
        bot_status["last_error"] = f"Login: {str(e)}"
        return False

def navigate_to_channel(driver, channel_id, channel_name="channel"):
    """Navigate to channel with robust error handling"""
    try:
        channel_url = f"https://discord.com/channels/@me/{channel_id}"
        
        logger.info(f"📍 Navigating to {channel_name}: {channel_id}")
        driver.get(channel_url)
        human_delay(5, 7)
        
        # Wait for channel to load - try multiple indicators
        wait = WebDriverWait(driver, 25)
        
        try:
            # Wait for message input box
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role='textbox']")))
            logger.info(f"✅ {channel_name} loaded successfully")
            return True
        except TimeoutException:
            # Try alternative indicator - messages container
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='messagesWrapper']")))
                logger.info(f"✅ {channel_name} loaded (messages view)")
                return True
            except:
                logger.warning(f"⚠️ {channel_name} loaded but elements not found")
                return True  # Proceed anyway
        
    except Exception as e:
        logger.error(f"❌ Failed to navigate to {channel_name}: {e}")
        bot_status["last_error"] = f"Navigate: {str(e)}"
        return False

def get_latest_message(driver):
    """Get latest message with multiple fallback strategies"""
    try:
        # Strategy 1: Recent message containers
        selectors = [
            "li[id^='chat-messages-']",
            "[class*='message_'][class*='cozyMessage']",
            "div[class*='messageListItem']",
            "[data-list-item-id^='chat-messages']"
        ]
        
        for selector in selectors:
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, selector)
                if messages and len(messages) > 0:
                    # Get last message
                    latest = messages[-1]
                    text_content = latest.text.strip()
                    
                    if text_content and len(text_content) > 0:
                        # Remove username/timestamp artifacts
                        lines = text_content.split('\n')
                        # Usually the actual message is in the last line(s)
                        message_text = '\n'.join(lines[-3:]).strip()
                        
                        if message_text:
                            logger.info(f"📨 Found message: {message_text[:50]}...")
                            return message_text
                            
            except Exception as e:
                continue
        
        logger.debug("No messages found with any selector")
        return None
        
    except Exception as e:
        logger.error(f"Error getting message: {e}")
        return None

def send_message(driver, text):
    """Send message with enhanced reliability"""
    try:
        if not text or len(text.strip()) == 0:
            logger.warning("Empty message, skipping")
            return False
        
        wait = WebDriverWait(driver, 20)
        
        # Find and click message input
        try:
            message_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[role='textbox']")))
        except TimeoutException:
            logger.error("Message input not found")
            return False
        
        message_input.click()
        human_delay(0.5, 1)
        
        # Clear existing content
        message_input.send_keys(Keys.CONTROL + "a")
        message_input.send_keys(Keys.BACKSPACE)
        human_delay(0.3, 0.6)
        
        # Type message with human-like speed
        type_like_human(message_input, text, clear_first=False)
        
        human_delay(0.5, 1)
        
        # Send message
        message_input.send_keys(Keys.RETURN)
        human_delay(1.5, 2.5)
        
        logger.info(f"✅ Message sent: {text[:50]}{'...' if len(text) > 50 else ''}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to send message: {e}")
        bot_status["last_error"] = f"Send: {str(e)}"
        return False

def keep_alive(driver, session_keeper):
    """Keep session active"""
    try:
        driver.execute_script("window.scrollBy(0, 50);")
        session_keeper.update_activity()
        return True
    except:
        return False

def monitor_and_forward():
    """Main monitoring loop with full error recovery"""
    logger.info("🚀 Starting Discord message forwarder...")
    bot_status["running"] = True
    
    session_keeper = SessionKeeper()
    driver = None
    last_message = None
    check_count = 0
    
    try:
        # Initialize driver
        driver = create_render_driver()
        if not driver:
            logger.error("Failed to create driver")
            return False
        
        # Login
        if not robust_login(driver):
            logger.error("Login failed")
            return False
        
        # Navigate to source channel
        if not navigate_to_channel(driver, SOURCE_CHANNEL_ID, "source"):
            logger.error("Cannot access source channel")
            return False
        
        logger.info("👀 Monitoring started successfully")
        logger.info(f"⏱️  Check interval: {CHECK_INTERVAL}s")
        
        # Main monitoring loop
        while True:
            check_count += 1
            bot_status["last_check"] = datetime.datetime.now().isoformat()
            
            # Check if session needs refresh
            if session_keeper.needs_refresh():
                logger.info("🔄 Session refresh needed")
                break
            
            # Keep session alive
            if not keep_alive(driver, session_keeper):
                session_keeper.record_failure()
                if session_keeper.needs_restart():
                    logger.error("Too many keep-alive failures")
                    break
            
            # Get latest message from source
            try:
                current_message = get_latest_message(driver)
                
                if current_message and current_message != last_message:
                    logger.info(f"🆕 New message detected!")
                    logger.info(f"Content: {current_message[:100]}...")
                    
                    # Navigate to destination channel
                    if navigate_to_channel(driver, DESTINATION_CHANNEL_ID, "destination"):
                        # Send message
                        if send_message(driver, current_message):
                            logger.info("✅ Message forwarded successfully!")
                            bot_status["messages_forwarded"] += 1
                            session_keeper.record_success()
                        else:
                            logger.error("Failed to send message")
                            session_keeper.record_failure()
                    else:
                        logger.error("Failed to reach destination")
                        session_keeper.record_failure()
                    
                    # Return to source channel
                    human_delay(2, 3)
                    navigate_to_channel(driver, SOURCE_CHANNEL_ID, "source")
                    human_delay(3, 4)
                    
                    last_message = current_message
                else:
                    session_keeper.record_success()
                    
            except Exception as e:
                logger.error(f"Error in check cycle: {e}")
                session_keeper.record_failure()
            
            # Status report
            if check_count % 10 == 0:
                status = "✅" if session_keeper.consecutive_failures == 0 else "⚠️"
                logger.info(f"{status} Check #{check_count} | Forwarded: {bot_status['messages_forwarded']} | Failures: {session_keeper.consecutive_failures}")
            
            # Check if restart needed
            if session_keeper.needs_restart():
                logger.error("❌ Too many consecutive failures, restarting...")
                break
            
            # Wait before next check
            time.sleep(CHECK_INTERVAL + random.uniform(-1, 2))
            
    except KeyboardInterrupt:
        logger.info("🛑 Stopped by user")
        return False
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}", exc_info=True)
        bot_status["last_error"] = str(e)
        return False
    finally:
        bot_status["running"] = False
        if driver:
            try:
                driver.quit()
                logger.info("🔚 Browser closed")
            except:
                pass
    
    return True

def main():
    """Main entry point with auto-restart"""
    logger.info("=" * 70)
    logger.info("🤖 Discord Message Forwarder - Render Optimized v2.0")
    logger.info(f"📅 Started: {datetime.datetime.now()}")
    logger.info(f"📤 Source Channel: {SOURCE_CHANNEL_ID}")
    logger.info(f"📥 Destination Channel: {DESTINATION_CHANNEL_ID}")
    logger.info(f"🌐 Web Dashboard: http://0.0.0.0:{os.environ.get('PORT', 10000)}")
    logger.info("=" * 70)
    
    # Give web server time to start
    time.sleep(3)
    
    attempt = 0
    max_attempts = 999  # Effectively infinite
    
    while attempt < max_attempts:
        attempt += 1
        logger.info(f"🔄 Session #{attempt}")
        
        try:
            success = monitor_and_forward()
            
            if not success:
                logger.warning(f"⚠️ Session ended, restarting in {RESTART_DELAY}s...")
                time.sleep(RESTART_DELAY)
            else:
                logger.info("Session completed normally")
                time.sleep(5)
                
        except Exception as e:
            logger.error(f"💥 Crash: {e}", exc_info=True)
            bot_status["last_error"] = str(e)
            time.sleep(RESTART_DELAY)
    
    # Keep web server alive
    logger.info("🌐 Keeping web server alive...")
    while True:
        time.sleep(300)
        logger.info(f"💓 Heartbeat | Forwarded: {bot_status['messages_forwarded']} | Errors: {bot_status['errors']}")

if __name__ == "__main__":
    main()
