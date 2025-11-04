from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
from flask import Flask, jsonify
import threading
import os
import time
import random
import datetime

# ====== WEB KEEP-ALIVE ======
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"status": "alive", "message": "Session manager running"})

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web, daemon=True).start()

# Configuration - HARDCODED
DISCORD_URL = "https://discord.com/login"
LOGIN_EMAIL = "solostudy110012@gmail.com"
LOGIN_PASSWORD = "JESUSBPS123@"
SOURCE_CHANNEL_ID = "1376365659830616207"
DESTINATION_CHANNEL_ID = "1435185554730782750"

class SessionKeeper:
    def __init__(self):
        self.last_activity = time.time()
        self.last_preventive_action = time.time()
        self.consecutive_stable_checks = 0
        
    def update_activity(self):
        self.last_activity = time.time()
        
    def should_perform_preventive_action(self):
        return time.time() - self.last_preventive_action > 300
        
    def record_stable_check(self):
        self.consecutive_stable_checks += 1
        
    def record_issue(self):
        self.consecutive_stable_checks = 0

def create_robust_driver():
    """Create driver with better anti-detection"""
    options = Options()
    
    # Anti-detection measures
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # More realistic user agent
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    # Additional stealth options
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-notifications")
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Hide webdriver property
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        print("✅ Chrome driver started successfully")
        return driver
    except Exception as e:
        print(f"❌ Driver creation failed: {e}")
        return None

def perform_preventive_maintenance(driver, session_keeper):
    """Perform actions to keep session alive"""
    try:
        print("🔧 Performing preventive maintenance...")
        
        # Gentle page interaction
        driver.execute_script("window.scrollBy(0, 50);")
        time.sleep(0.5)
        driver.execute_script("window.scrollBy(0, -50);")
        
        # Ensure we're in the correct channel
        current_url = driver.current_url
        if SOURCE_CHANNEL_ID not in current_url:
            print("⚠️ Not in source channel, navigating back...")
            join_channel_by_id(driver, SOURCE_CHANNEL_ID)
        
        session_keeper.last_preventive_action = time.time()
        session_keeper.record_stable_check()
        print("✅ Preventive maintenance completed")
        return True
        
    except Exception as e:
        print(f"⚠️ Preventive maintenance failed: {e}")
        session_keeper.record_issue()
        return False

def keep_session_active(driver, session_keeper):
    """Continuous session maintenance"""
    try:
        # Check if we need preventive action
        if session_keeper.should_perform_preventive_action():
            return perform_preventive_maintenance(driver, session_keeper)
        
        # Lightweight heartbeat
        session_keeper.update_activity()
        
        # Occasionally perform very light activity
        if random.random() < 0.1:
            driver.execute_script("""
                const evt = new KeyboardEvent('keydown', {key: 'Shift'});
                document.dispatchEvent(evt);
            """)
        
        session_keeper.record_stable_check()
        return True
        
    except Exception as e:
        print(f"⚠️ Session keep-alive failed: {e}")
        session_keeper.record_issue()
        return False

def verify_session_health(driver):
    """Check if session is still valid"""
    try:
        current_url = driver.current_url
        if not current_url or "login" in current_url.lower():
            return False
            
        # Check if we can find message input
        try:
            driver.find_element(By.CSS_SELECTOR, "[role='textbox']")
            return True
        except NoSuchElementException:
            return False
            
    except Exception:
        return False

def robust_login(driver):
    """Login with improved error handling"""
    try:
        print("🔐 Starting login process...")
        driver.get(DISCORD_URL)
        time.sleep(random.uniform(3, 5))
        
        wait = WebDriverWait(driver, 20)
        
        # Wait for and fill email
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        email_field.clear()
        time.sleep(0.5)
        
        for char in LOGIN_EMAIL:
            email_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.12))
        
        time.sleep(random.uniform(0.5, 1))
        
        # Wait for and fill password
        password_field = driver.find_element(By.NAME, "password")
        password_field.clear()
        time.sleep(0.5)
        
        for char in LOGIN_PASSWORD:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.12))
        
        time.sleep(random.uniform(1, 2))
        
        # Submit
        password_field.send_keys(Keys.RETURN)
        print("📤 Login form submitted...")
        
        # Wait for login to complete - look for main app interface
        time.sleep(8)  # Give Discord time to load
        
        # Verify we're logged in
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[role='textbox'], textarea")))
        
        print("✅ Login successful")
        return True
        
    except TimeoutException:
        print("❌ Login timeout - Discord may require verification")
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
            time.sleep(random.uniform(4, 6))
        
        # Verify channel loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[role='textbox']"))
        )
        
        print(f"✅ Successfully joined channel: {channel_id}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to join channel {channel_id}: {e}")
        return False

def get_current_message_count(driver):
    """Get current message count"""
    try:
        # Updated selectors for Discord's current structure
        message_selectors = [
            "li[id*='chat-messages']",
            "[class*='message-']",
            "[class*='cozy-']",
            "div[class*='messageListItem']"
        ]
        
        for selector in message_selectors:
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, selector)
                if messages and len(messages) > 0:
                    return len(messages)
            except:
                continue
        
        return 0
    except Exception as e:
        print(f"⚠️ Error counting messages: {e}")
        return 0

def get_latest_message_element(driver):
    """Get the most recent message element"""
    try:
        message_selectors = [
            "li[id*='chat-messages']",
            "[class*='message-']",
            "[class*='cozy-']"
        ]
        
        for selector in message_selectors:
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, selector)
                if messages and len(messages) > 0:
                    return messages[-1]
            except:
                continue
        
        return None
    except Exception as e:
        print(f"⚠️ Error getting latest message: {e}")
        return None

def extract_message_data(message_element):
    """Extract text from message element"""
    try:
        # Try multiple selectors for message content
        text_selectors = [
            "[class*='messageContent']",
            "[class*='markup']",
            "div[class*='content-']"
        ]
        
        text = ""
        for selector in text_selectors:
            try:
                content_elem = message_element.find_element(By.CSS_SELECTOR, selector)
                text = content_elem.text
                if text and len(text.strip()) > 0:
                    break
            except:
                continue
        
        # Fallback to element text
        if not text:
            text = message_element.text
        
        return text.strip()
    except Exception as e:
        print(f"⚠️ Error extracting message: {e}")
        return ""

def send_message(driver, text):
    """Send message to current channel"""
    try:
        wait = WebDriverWait(driver, 15)
        
        # Find message input
        input_selectors = [
            "[role='textbox']",
            "div[contenteditable='true']",
            "textarea"
        ]
        
        message_input = None
        for selector in input_selectors:
            try:
                message_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break
            except:
                continue
        
        if not message_input:
            print("❌ Could not find message input")
            return False
        
        # Click and clear
        message_input.click()
        time.sleep(0.5)
        message_input.send_keys(Keys.CONTROL + "a")
        message_input.send_keys(Keys.BACKSPACE)
        time.sleep(0.3)
        
        # Type message with human-like delays
        for char in text:
            message_input.send_keys(char)
            if random.random() < 0.15:
                time.sleep(random.uniform(0.02, 0.08))
        
        time.sleep(random.uniform(0.3, 0.7))
        
        # Send
        message_input.send_keys(Keys.RETURN)
        time.sleep(1)
        
        print(f"✅ Message sent: {text[:50]}{'...' if len(text) > 50 else ''}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

def monitor_messages_with_prevention():
    """Main monitoring loop"""
    print("🚀 Starting Discord message monitor...")
    
    session_keeper = SessionKeeper()
    driver = create_robust_driver()
    
    if not driver:
        print("❌ Failed to create driver")
        return
    
    if not robust_login(driver):
        print("❌ Login failed")
        driver.quit()
        return
    
    # Navigate to source channel
    if not join_channel_by_id(driver, SOURCE_CHANNEL_ID):
        print("❌ Cannot access source channel")
        driver.quit()
        return
    
    # Get initial message count
    time.sleep(3)
    initial_count = get_current_message_count(driver)
    print(f"📊 Starting monitor - ignoring {initial_count} existing messages")
    
    last_message_count = initial_count
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # Keep session alive
            if not keep_session_active(driver, session_keeper):
                if not verify_session_health(driver):
                    print("❌ Session unhealthy, attempting recovery...")
                    if not join_channel_by_id(driver, SOURCE_CHANNEL_ID):
                        print("💥 Recovery failed, restarting...")
                        break
            
            # Check for new messages
            current_count = get_current_message_count(driver)
            
            if current_count > last_message_count:
                new_message_count = current_count - last_message_count
                print(f"📨 Detected {new_message_count} new message(s)!")
                
                # Get latest message
                latest_message = get_latest_message_element(driver)
                if latest_message:
                    text = extract_message_data(latest_message)
                    
                    if text and len(text.strip()) > 0:
                        print(f"📝 Message content: {text[:100]}...")
                        
                        # Navigate to destination and send
                        if join_channel_by_id(driver, DESTINATION_CHANNEL_ID):
                            if send_message(driver, text):
                                print("✅ Message forwarded successfully!")
                            else:
                                print("❌ Failed to forward message")
                        
                        # Return to source channel
                        time.sleep(1)
                        join_channel_by_id(driver, SOURCE_CHANNEL_ID)
                        time.sleep(2)
                        
                        # Update count after returning
                        last_message_count = get_current_message_count(driver)
                    else:
                        last_message_count = current_count
                else:
                    last_message_count = current_count
            
            # Status update
            if check_count % 20 == 0:
                print(f"👀 Monitor active - Check #{check_count} | Stable: {session_keeper.consecutive_stable_checks}")
            
            # Adaptive wait time
            if session_keeper.consecutive_stable_checks > 10:
                wait_time = random.uniform(2, 4)
            else:
                wait_time = random.uniform(4, 6)
            
            time.sleep(wait_time)
            
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

def main():
    print("=" * 60)
    print("🤖 Discord Message Forwarder Bot")
    print(f"📅 Started: {datetime.datetime.now()}")
    print(f"📤 Source Channel: {SOURCE_CHANNEL_ID}")
    print(f"📥 Destination Channel: {DESTINATION_CHANNEL_ID}")
    print("=" * 60)
    
    try:
        monitor_messages_with_prevention()
    except Exception as e:
        print(f"💥 Main error: {e}")
    finally:
        print(f"\n📅 Ended: {datetime.datetime.now()}")
        print("=" * 60)

if __name__ == "__main__":
    main()
