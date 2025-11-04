from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from flask import Flask, jsonify
import threading
import os
import time
import random
import datetime
import requests

# ====== WEB KEEP-ALIVE ======
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "alive", "message": "Session manager running"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# Configuration
DISCORD_URL = "https://discord.com/login"
LOGIN_EMAIL = "solostudy110012@gmail.com"
LOGIN_PASSWORD = "JESUSBPS123@"
SOURCE_CHANNEL_ID = "1376365659830616207"
DESTINATION_CHANNEL_ID = "1435185554730782750"

class SessionKeeper:
    def __init__(self):
        self.last_activity = time.time()
        self.consecutive_failures = 0
        
    def update_activity(self):
        self.last_activity = time.time()
        
    def record_success(self):
        self.consecutive_failures = 0
        
    def record_failure(self):
        self.consecutive_failures += 1
        
    def needs_restart(self):
        return self.consecutive_failures >= 3

def create_render_driver():
    """Create Chrome driver optimized for Render environment"""
    options = Options()
    
    # Render-specific configuration
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    
    # Headless mode for Render
    options.add_argument("--headless=new")
    
    # Window size
    options.add_argument("--window-size=1920,1080")
    
    # Anti-detection
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # User agent
    user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    
    try:
        # For Render environment
        service = Service()
        driver = webdriver.Chrome(service=service, options=options)
        
        # Stealth modifications
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver created successfully for Render")
        return driver
        
    except Exception as e:
        print(f"❌ Failed to create Chrome driver: {e}")
        return None

def human_like_delay(min_sec=0.1, max_sec=0.3):
    """Human-like random delay"""
    time.sleep(random.uniform(min_sec, max_sec))

def robust_login(driver):
    """Login to Discord"""
    try:
        print("🔐 Starting login process...")
        driver.get(DISCORD_URL)
        time.sleep(5)
        
        wait = WebDriverWait(driver, 30)
        
        # Find email field
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.clear()
        human_like_delay(0.5, 1)
        
        # Type email
        for char in LOGIN_EMAIL:
            email_field.send_keys(char)
            human_like_delay(0.05, 0.1)
        
        human_like_delay(1, 2)
        
        # Find password field
        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        human_like_delay(0.5, 1)
        
        # Type password
        for char in LOGIN_PASSWORD:
            password_field.send_keys(char)
            human_like_delay(0.05, 0.1)
        
        human_like_delay(1, 2)
        
        # Submit login
        password_field.send_keys(Keys.RETURN)
        print("📤 Login submitted...")
        
        # Wait for login to complete
        time.sleep(10)
        
        # Check if login was successful
        if "channels" in driver.current_url or "login" not in driver.current_url:
            print("✅ Login successful")
            return True
        else:
            print("❌ Login may have failed")
            return False
            
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def join_channel_by_id(driver, channel_id):
    """Navigate to specific channel"""
    try:
        channel_url = f"https://discord.com/channels/@me/{channel_id}"
        
        if channel_id not in driver.current_url:
            print(f"📍 Navigating to channel: {channel_id}")
            driver.get(channel_url)
            time.sleep(5)
        
        # Wait for channel to load
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role='textbox']")))
        
        print(f"✅ Successfully joined channel: {channel_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to join channel {channel_id}: {e}")
        return False

def get_latest_message_content(driver):
    """Get the latest message content"""
    try:
        # Try multiple message selectors
        message_selectors = [
            "[class*='message_']",
            "li[class*='message_']",
            "div[class*='message_']"
        ]
        
        for selector in message_selectors:
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, selector)
                if messages:
                    latest_message = messages[-1]
                    text = latest_message.text
                    if text and len(text.strip()) > 0:
                        return text.strip()
            except:
                continue
                
        return None
    except Exception as e:
        print(f"⚠️ Error getting latest message: {e}")
        return None

def send_message_to_channel(driver, text):
    """Send message to current channel"""
    try:
        if not text:
            return False
            
        wait = WebDriverWait(driver, 15)
        
        # Find message input
        message_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "[role='textbox']")))
        
        # Clear and type message
        message_input.click()
        human_like_delay(0.5, 1)
        message_input.send_keys(Keys.CONTROL + "a")
        message_input.send_keys(Keys.BACKSPACE)
        human_like_delay(0.5, 1)
        
        # Type message
        for char in text:
            message_input.send_keys(char)
            if random.random() < 0.1:
                human_like_delay(0.02, 0.05)
        
        human_like_delay(0.5, 1)
        
        # Send
        message_input.send_keys(Keys.RETURN)
        human_like_delay(1, 2)
        
        print(f"✅ Message sent: {text[:50]}{'...' if len(text) > 50 else ''}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

def keep_session_alive(driver, session_keeper):
    """Keep the session active"""
    try:
        # Simple activity to keep session alive
        driver.execute_script("window.scrollBy(0, 100);")
        session_keeper.update_activity()
        session_keeper.record_success()
        return True
    except:
        session_keeper.record_failure()
        return False

def monitor_messages():
    """Main monitoring function"""
    print("🚀 Starting Discord message monitor...")
    
    session_keeper = SessionKeeper()
    driver = create_render_driver()
    
    if not driver:
        print("❌ Failed to create browser driver")
        return False
    
    # Login
    if not robust_login(driver):
        print("❌ Login failed")
        driver.quit()
        return False
    
    # Navigate to source channel
    if not join_channel_by_id(driver, SOURCE_CHANNEL_ID):
        print("❌ Cannot access source channel")
        driver.quit()
        return False
    
    print("👀 Starting message monitoring...")
    last_message = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # Keep session alive
            if not keep_session_alive(driver, session_keeper):
                if session_keeper.needs_restart():
                    print("🔄 Too many failures, restarting...")
                    break
            
            # Check for new messages
            current_message = get_latest_message_content(driver)
            
            if current_message and current_message != last_message:
                print(f"📨 New message detected: {current_message[:100]}...")
                
                # Forward to destination
                if join_channel_by_id(driver, DESTINATION_CHANNEL_ID):
                    if send_message_to_channel(driver, current_message):
                        print("✅ Message forwarded successfully!")
                    else:
                        print("❌ Failed to forward message")
                
                # Return to source
                time.sleep(2)
                join_channel_by_id(driver, SOURCE_CHANNEL_ID)
                time.sleep(3)
                
                last_message = current_message
            
            # Status update every 10 checks
            if check_count % 10 == 0:
                status = "✅" if session_keeper.consecutive_failures == 0 else "⚠️"
                print(f"{status} Check #{check_count} | Failures: {session_keeper.consecutive_failures}")
            
            # Wait before next check
            time.sleep(random.uniform(5, 8))
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
            print("🔚 Browser closed")
        except:
            pass
    
    return True

def main():
    """Main function with restart logic"""
    print("=" * 60)
    print("🤖 Discord Message Forwarder Bot - Render Optimized")
    print(f"📅 Started: {datetime.datetime.now()}")
    print(f"📤 Source: {SOURCE_CHANNEL_ID}")
    print(f"📥 Destination: {DESTINATION_CHANNEL_ID}")
    print("=" * 60)
    
    max_attempts = 3
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"\n🔄 Attempt {attempt}/{max_attempts}")
        
        try:
            success = monitor_messages()
            if success:
                print("✅ Monitor completed successfully")
                break
            else:
                print("❌ Monitor failed, will retry...")
                time.sleep(10)
        except Exception as e:
            print(f"💥 Crash detected: {e}")
            if attempt < max_attempts:
                print("🔄 Restarting...")
                time.sleep(10)
    
    if attempt >= max_attempts:
        print("❌ Maximum attempts reached, service will remain alive for web requests")
        print("💡 The web server is still running at https://forwarder-j50q.onrender.com")
        
        # Keep the web server running indefinitely
        while True:
            time.sleep(60)
            print("🌐 Web server still running...")
    
    print(f"📅 Ended: {datetime.datetime.now()}")
    print("=" * 60)

if __name__ == "__main__":
    main()
