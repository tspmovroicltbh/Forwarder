from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
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
        self.last_maintenance = time.time()
        self.consecutive_failures = 0
        self.message_count = 0
        self.last_known_message_id = None
        
    def update_activity(self):
        self.last_activity = time.time()
        
    def should_perform_maintenance(self):
        return time.time() - self.last_maintenance > 300  # 5 minutes
        
    def record_success(self):
        self.consecutive_failures = 0
        
    def record_failure(self):
        self.consecutive_failures += 1
        
    def needs_restart(self):
        return self.consecutive_failures >= 3

def create_stealth_driver():
    """Create a stealthy Chrome driver to avoid detection"""
    options = Options()
    
    # Stealth options
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    
    # Realistic user agent and behavior
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    options.add_argument(f"--user-agent={user_agent}")
    
    # Additional stealth settings
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--disable-popup-blocking")
    
    # Comment out headless for debugging, uncomment for production
    # options.add_argument("--headless=new")
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Execute CDP commands to hide automation
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": user_agent,
            "platform": "Windows"
        })
        
        # Remove webdriver property
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        print("✅ Stealth Chrome driver created successfully")
        return driver
        
    except Exception as e:
        print(f"❌ Failed to create driver: {e}")
        return None

def human_like_delay(min_sec=0.1, max_sec=0.3):
    """Human-like random delay"""
    time.sleep(random.uniform(min_sec, max_sec))

def human_like_typing(element, text):
    """Type text with human-like randomness"""
    element.click()
    human_like_delay(0.2, 0.5)
    
    for char in text:
        element.send_keys(char)
        # Variable typing speed
        if random.random() < 0.3:  # 30% chance of pause
            human_like_delay(0.05, 0.15)
        else:
            human_like_delay(0.02, 0.08)
    
    human_like_delay(0.3, 0.7)

def perform_random_activity(driver):
    """Perform random human-like activities"""
    try:
        actions = [
            lambda: driver.execute_script("window.scrollBy(0, 100);"),
            lambda: driver.execute_script("window.scrollBy(0, -50);"),
            lambda: ActionChains(driver).send_keys(Keys.PAGE_UP).perform(),
            lambda: ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform(),
        ]
        
        random.choice(actions)()
        human_like_delay(0.5, 1.5)
        return True
    except:
        return False

def robust_login(driver):
    """Improved login with better error handling"""
    try:
        print("🔐 Starting login process...")
        driver.get(DISCORD_URL)
        human_like_delay(3, 5)
        
        wait = WebDriverWait(driver, 25)
        
        # Wait for email field with multiple selectors
        email_selectors = [
            "input[name='email']",
            "input[type='email']",
            "input[aria-label*='Email']",
            "input[placeholder*='Email']"
        ]
        
        email_field = None
        for selector in email_selectors:
            try:
                email_field = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break
            except:
                continue
        
        if not email_field:
            print("❌ Could not find email field")
            return False
        
        # Human-like email entry
        print("📧 Entering email...")
        human_like_typing(email_field, LOGIN_EMAIL)
        
        # Find password field
        password_selectors = [
            "input[name='password']",
            "input[type='password']",
            "input[aria-label*='Password']"
        ]
        
        password_field = None
        for selector in password_selectors:
            try:
                password_field = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if not password_field:
            print("❌ Could not find password field")
            return False
        
        # Human-like password entry
        print("🔒 Entering password...")
        human_like_typing(password_field, LOGIN_PASSWORD)
        
        # Find and click login button
        login_selectors = [
            "button[type='submit']",
            "button[class*='login']",
            "div[class*='submit'] button"
        ]
        
        login_button = None
        for selector in login_selectors:
            try:
                login_button = driver.find_element(By.CSS_SELECTOR, selector)
                break
            except:
                continue
        
        if login_button:
            login_button.click()
            print("📤 Login button clicked")
        else:
            # Fallback to Enter key
            password_field.send_keys(Keys.RETURN)
            print("📤 Login submitted with Enter key")
        
        # Wait for login to complete
        print("⏳ Waiting for login to complete...")
        human_like_delay(8, 12)
        
        # Verify login success with multiple checks
        success_indicators = [
            "[class*='channels']",
            "[class*='guilds']",
            "[class*='sidebar']",
            "div[aria-label*='Server']"
        ]
        
        for indicator in success_indicators:
            try:
                driver.find_element(By.CSS_SELECTOR, indicator)
                print("✅ Login successful")
                return True
            except:
                continue
        
        # Check if we're still on login page
        if "login" in driver.current_url.lower():
            print("❌ Still on login page - login may have failed")
            return False
            
        print("✅ Login likely successful (alternative indicators found)")
        return True
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def join_channel_by_id(driver, channel_id):
    """Navigate to specific channel with improved reliability"""
    try:
        channel_url = f"https://discord.com/channels/@me/{channel_id}"
        
        if channel_id not in driver.current_url:
            print(f"📍 Navigating to channel: {channel_id}")
            driver.get(channel_url)
            human_like_delay(4, 7)
        
        # Wait for channel to load with multiple indicators
        wait = WebDriverWait(driver, 20)
        
        # Check for message input or chat area
        channel_indicators = [
            "[role='textbox'][aria-label*='Message']",
            "div[contenteditable='true'][aria-label*='Message']",
            "[class*='messageInput']",
            "[class*='chatContent']"
        ]
        
        for indicator in channel_indicators:
            try:
                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, indicator)))
                print(f"✅ Successfully joined channel: {channel_id}")
                return True
            except:
                continue
        
        print(f"⚠️ Channel joined but couldn't verify loading: {channel_id}")
        return True  # Still return True as navigation likely succeeded
        
    except Exception as e:
        print(f"❌ Failed to join channel {channel_id}: {e}")
        return False

def get_message_elements(driver):
    """Get all message elements with updated selectors"""
    try:
        message_selectors = [
            "[data-list-id='chat-messages'] > li",
            "[class*='message_']",
            "div[class*='message_']",
            "article[class*='message_']",
            "li[class*='message_']"
        ]
        
        for selector in message_selectors:
            try:
                messages = driver.find_elements(By.CSS_SELECTOR, selector)
                if messages and len(messages) > 0:
                    return messages
            except:
                continue
        
        return []
    except Exception as e:
        print(f"⚠️ Error getting messages: {e}")
        return []

def extract_message_content(message_element):
    """Extract text content from message element"""
    try:
        # Try multiple content selectors
        content_selectors = [
            "[class*='messageContent']",
            "[class*='content_']",
            "div[class*='markup_']",
            "div[class*='content_']",
            "span[class*='content_']"
        ]
        
        for selector in content_selectors:
            try:
                content_elem = message_element.find_element(By.CSS_SELECTOR, selector)
                text = content_elem.text.strip()
                if text:
                    return text
            except:
                continue
        
        # Fallback to entire element text
        full_text = message_element.text.strip()
        if full_text:
            return full_text
            
        return ""
    except Exception as e:
        print(f"⚠️ Error extracting message content: {e}")
        return ""

def get_latest_message_content(driver):
    """Get the content of the most recent message"""
    try:
        messages = get_message_elements(driver)
        if not messages:
            return None
            
        latest_message = messages[-1]
        content = extract_message_content(latest_message)
        
        if content:
            return content
        else:
            return None
            
    except Exception as e:
        print(f"⚠️ Error getting latest message: {e}")
        return None

def send_message_to_channel(driver, text):
    """Send message to current channel with improved reliability"""
    try:
        if not text or len(text.strip()) == 0:
            print("❌ Empty message, not sending")
            return False
            
        wait = WebDriverWait(driver, 15)
        
        # Find message input with multiple selectors
        input_selectors = [
            "[role='textbox'][aria-label*='Message']",
            "div[contenteditable='true'][aria-label*='Message']",
            "[class*='messageInput'] textarea",
            "[class*='slateTextArea']"
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
        
        # Clear input
        message_input.click()
        human_like_delay(0.3, 0.7)
        
        # Select all and clear (multiple methods)
        try:
            message_input.send_keys(Keys.CONTROL + "a")
        except:
            try:
                message_input.clear()
            except:
                pass
        
        human_like_delay(0.2, 0.5)
        
        # Type message with human-like behavior
        print(f"💬 Typing message: {text[:50]}{'...' if len(text) > 50 else ''}")
        human_like_typing(message_input, text)
        
        # Send message
        human_like_delay(0.5, 1.0)
        message_input.send_keys(Keys.RETURN)
        human_like_delay(1, 2)
        
        print("✅ Message sent successfully")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

def perform_maintenance(driver, session_keeper):
    """Perform maintenance activities to keep session alive"""
    try:
        print("🔧 Performing maintenance...")
        session_keeper.last_maintenance = time.time()
        
        # Random activities
        perform_random_activity(driver)
        
        # Ensure we're in source channel
        if SOURCE_CHANNEL_ID not in driver.current_url:
            print("🔄 Returning to source channel...")
            join_channel_by_id(driver, SOURCE_CHANNEL_ID)
            human_like_delay(2, 4)
        
        session_keeper.record_success()
        print("✅ Maintenance completed")
        return True
        
    except Exception as e:
        print(f"⚠️ Maintenance failed: {e}")
        session_keeper.record_failure()
        return False

def monitor_and_forward_messages():
    """Main monitoring loop with improved reliability"""
    print("🚀 Starting Discord message monitor...")
    
    session_keeper = SessionKeeper()
    driver = create_stealth_driver()
    
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
    last_known_content = None
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # Perform maintenance if needed
            if session_keeper.should_perform_maintenance():
                if not perform_maintenance(driver, session_keeper):
                    if session_keeper.needs_restart():
                        print("🔄 Too many failures, restarting...")
                        break
            
            # Check for new messages
            current_content = get_latest_message_content(driver)
            
            if current_content and current_content != last_known_content:
                print(f"📨 New message detected: {current_content[:100]}...")
                
                # Forward to destination channel
                if join_channel_by_id(driver, DESTINATION_CHANNEL_ID):
                    if send_message_to_channel(driver, current_content):
                        print("✅ Message forwarded successfully!")
                    else:
                        print("❌ Failed to forward message")
                
                # Return to source channel
                human_like_delay(1, 2)
                join_channel_by_id(driver, SOURCE_CHANNEL_ID)
                human_like_delay(2, 3)
                
                last_known_content = current_content
            
            # Status updates
            if check_count % 10 == 0:
                status = "✅" if session_keeper.consecutive_failures == 0 else "⚠️"
                print(f"{status} Monitor active - Check #{check_count} | Failures: {session_keeper.consecutive_failures}")
            
            # Adaptive delay based on stability
            if session_keeper.consecutive_failures == 0:
                delay = random.uniform(3, 6)  # Shorter delay when stable
            else:
                delay = random.uniform(6, 10)  # Longer delay when unstable
            
            time.sleep(delay)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopped by user")
    except Exception as e:
        print(f"💥 Fatal error in monitoring: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            driver.quit()
            print("🔚 Browser closed")
        except:
            pass

def main():
    """Main function with restart capability"""
    print("=" * 60)
    print("🤖 Discord Message Forwarder Bot")
    print(f"📅 Started: {datetime.datetime.now()}")
    print(f"📤 Source: {SOURCE_CHANNEL_ID}")
    print(f"📥 Destination: {DESTINATION_CHANNEL_ID}")
    print("=" * 60)
    
    restart_count = 0
    max_restarts = 5
    
    while restart_count < max_restarts:
        try:
            if monitor_and_forward_messages():
                print("✅ Monitor completed successfully")
                break
            else:
                restart_count += 1
                print(f"🔄 Restarting... ({restart_count}/{max_restarts})")
                time.sleep(10)
        except Exception as e:
            restart_count += 1
            print(f"💥 Crash detected, restarting... ({restart_count}/{max_restarts})")
            print(f"Error: {e}")
            time.sleep(10)
    
    if restart_count >= max_restarts:
        print("❌ Maximum restarts reached, giving up")
    
    print(f"📅 Ended: {datetime.datetime.now()}")
    print("=" * 60)

if __name__ == "__main__":
    main()
