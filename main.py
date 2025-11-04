from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, TimeoutException
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime

# Configuration
DISCORD_URL = "https://discord.com"
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
        """Check if it's time to perform preventive action"""
        return time.time() - self.last_preventive_action > 300  # 5 minutes
        
    def record_stable_check(self):
        self.consecutive_stable_checks += 1
        
    def record_issue(self):
        self.consecutive_stable_checks = 0

def create_robust_driver():
    """Create a WebDriver with maximum stability options"""
    options = webdriver.ChromeOptions()
    
    # Core stability options
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    
    # Memory and performance
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-images")  # Reduce memory usage
    options.add_argument("--aggressive-cache-discard")
    options.add_argument("--memory-pressure-off")
    
    # Network stability
    options.add_argument("--disable-background-timer-throttling")
    options.add_argument("--disable-renderer-backgrounding")
    options.add_argument("--disable-backgrounding-occluded-windows")
    
    # Session persistence
    options.add_argument("--disable-session-crashed-bubble")
    options.add_argument("--disable-features=VizDisplayCompositor")
    options.add_argument("--disable-component-extensions-with-background-pages")
    
    # User data persistence (critical for session maintenance)
    options.add_argument("--user-data-dir=./discord_session")
    options.add_argument("--profile-directory=Default")
    
    options.add_argument("--window-size=1200,800")
    
    try:
        driver = webdriver.Chrome(options=options)
        
        # Stealth scripts
        driver.execute_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            // Prevent session timeout by simulating real user
            setInterval(() => {
                const evt = new MouseEvent('mousemove', {
                    clientX: Math.random() * window.innerWidth,
                    clientY: Math.random() * window.innerHeight
                });
                document.dispatchEvent(evt);
            }, 60000); // Move mouse every minute
        """)
        
        return driver
    except Exception as e:
        print(f"❌ Driver creation failed: {e}")
        return None

def perform_preventive_maintenance(driver, session_keeper):
    """Perform actions to keep session alive and healthy"""
    try:
        print("🔧 Performing preventive maintenance...")
        
        # 1. Refresh the page gently (without losing data)
        driver.execute_script("location.reload(true);")
        time.sleep(random.uniform(3, 5))
        
        # 2. Clear any potential memory buildup
        driver.execute_script("""
            if (window.performance && window.performance.memory) {
                console.log('Memory usage:', window.performance.memory);
            }
            // Clear any console logs that might accumulate
            console.clear();
        """)
        
        # 3. Ensure we're still in the correct channel
        if SOURCE_CHANNEL_ID not in driver.current_url:
            join_channel_by_id(driver, SOURCE_CHANNEL_ID)
        
        # 4. Perform gentle interactions
        driver.execute_script("window.scrollBy(0, 10);")
        time.sleep(0.5)
        driver.execute_script("window.scrollBy(0, -10);")
        
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
        
        # Lightweight heartbeat - just update activity timestamp
        session_keeper.update_activity()
        
        # Occasionally perform very light activity
        if random.random() < 0.1:  # 10% chance
            driver.execute_script("""
                // Minimal activity to keep connection alive
                if (document.hasFocus()) {
                    const evt = new KeyboardEvent('keydown', {key: 'Shift'});
                    document.dispatchEvent(evt);
                }
            """)
        
        session_keeper.record_stable_check()
        return True
        
    except Exception as e:
        print(f"⚠️ Session keep-alive failed: {e}")
        session_keeper.record_issue()
        return False

def verify_session_health(driver):
    """Comprehensive session health check"""
    try:
        # 1. Check if browser is responsive
        current_url = driver.current_url
        if not current_url:
            return False
            
        # 2. Check if we're still logged in
        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 
                    "textarea, [role='textbox'], [contenteditable='true']"))
            )
        except:
            return False
            
        # 3. Check if page is loaded and functional
        ready_state = driver.execute_script("return document.readyState;")
        if ready_state != "complete":
            return False
            
        # 4. Check for any error dialogs or login prompts
        page_source = driver.page_source.lower()
        if "login" in page_source and "password" in page_source:
            return False
            
        return True
        
    except Exception:
        return False

def robust_login(driver):
    """Login with persistent session management"""
    try:
        # Try to use existing session first
        driver.get(f"{DISCORD_URL}/channels/@me")
        time.sleep(3)
        
        # Check if we're already logged in
        if verify_session_health(driver):
            print("✅ Using existing session")
            return True
        
        # If not logged in, perform fresh login
        print("🔐 Starting fresh login...")
        driver.get(DISCORD_URL)
        time.sleep(random.uniform(2, 4))
        
        wait = WebDriverWait(driver, 15)
        email_field = wait.until(EC.presence_of_element_located((By.NAME, "email")))
        password_field = wait.until(EC.presence_of_element_located((By.NAME, "password")))
        
        # Human-like typing
        email_field.clear()
        for char in LOGIN_EMAIL:
            email_field.send_keys(char)
            time.sleep(random.uniform(0.03, 0.08))
        
        time.sleep(random.uniform(0.5, 1))
        
        password_field.clear()
        for char in LOGIN_PASSWORD:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.03, 0.08))
        
        time.sleep(random.uniform(0.5, 1))
        password_field.send_keys(Keys.RETURN)
        
        # Wait for login to complete
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, [role='textbox']"))
        )
        
        print("✅ Login successful")
        return True
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False

def join_channel_by_id(driver, channel_id):
    """Navigate to channel with health checks"""
    try:
        channel_url = f"{DISCORD_URL}/channels/@me/{channel_id}"
        
        # Only navigate if we're not already there
        if channel_id not in driver.current_url:
            driver.get(channel_url)
            time.sleep(random.uniform(3, 5))
        
        # Verify we're in the channel
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "textarea, [role='textbox']"))
        )
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to join channel: {e}")
        return False

def get_current_message_count(driver):
    """Get message count with health check"""
    try:
        message_selectors = [
            "[class*='message']",
            "[data-list-item-id*='messages']",
            "[class*='messageGroup']"
        ]
        
        for selector in message_selectors:
            try:
                messages = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                return len(messages)
            except:
                continue
        return 0
    except Exception:
        return 0

def get_latest_message_element(driver):
    """Get latest message with health check"""
    try:
        message_selectors = [
            "[class*='message']",
            "[data-list-item-id*='messages']",
            "[class*='messageGroup']"
        ]
        
        for selector in message_selectors:
            try:
                messages = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if messages:
                    return messages[-1]
            except:
                continue
        return None
    except Exception:
        return None

def extract_message_data(message_element):
    """Extract message text"""
    try:
        text_selectors = [
            "[class*='messageContent']",
            "[class*='content']",
            "[class*='markup']"
        ]
        
        text = ""
        for selector in text_selectors:
            try:
                content_elem = message_element.find_element(By.CSS_SELECTOR, selector)
                text = content_elem.text
                if text:
                    break
            except:
                continue
        
        if not text:
            text = message_element.text
        
        return text.strip()
    except Exception:
        return ""

def send_message(driver, text):
    """Send message with health checks"""
    try:
        wait = WebDriverWait(driver, 10)
        input_selectors = [
            "textarea[data-slate-object='block']",
            "textarea[aria-label*='Message']",
            "[role='textbox']"
        ]
        
        message_input = None
        for selector in input_selectors:
            try:
                message_input = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                break
            except:
                continue
        
        if not message_input:
            return False
        
        message_input.click()
        message_input.clear()
        
        # Type message
        for char in text:
            message_input.send_keys(char)
            if random.random() < 0.1:
                time.sleep(random.uniform(0.01, 0.05))
        
        time.sleep(random.uniform(0.2, 0.5))
        message_input.send_keys(Keys.RETURN)
        
        print(f"✅ Message sent: {text[:50]}{'...' if len(text) > 50 else ''}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send message: {e}")
        return False

def monitor_messages_with_prevention():
    """Main monitoring loop that prevents session death"""
    print("🚀 Starting preventive session management...")
    
    session_keeper = SessionKeeper()
    driver = create_robust_driver()
    
    if not driver or not robust_login(driver):
        print("❌ Initialization failed")
        return
    
    # Initial channel setup
    if not join_channel_by_id(driver, SOURCE_CHANNEL_ID):
        print("❌ Cannot access source channel")
        driver.quit()
        return
    
    initial_count = get_current_message_count(driver)
    print(f"📊 Ignoring {initial_count} existing messages")
    
    last_message_count = initial_count
    check_count = 0
    
    try:
        while True:
            check_count += 1
            
            # 1. PREVENTIVE: Keep session alive (always run this first)
            if not keep_session_active(driver, session_keeper):
                print("⚠️ Session maintenance issue detected")
                # Try to recover gently without full restart
                if not verify_session_health(driver):
                    print("🔧 Attempting gentle recovery...")
                    if not join_channel_by_id(driver, SOURCE_CHANNEL_ID):
                        print("❌ Recovery failed, need restart")
                        break
            
            # 2. Check for new messages
            current_count = get_current_message_count(driver)
            
            if current_count > last_message_count:
                new_message_count = current_count - last_message_count
                print(f"📨 {new_message_count} new message(s) detected")
                
                latest_message = get_latest_message_element(driver)
                if latest_message:
                    text = extract_message_data(latest_message)
                    
                    if text and len(text.strip()) > 0:
                        print(f"📝 Forwarding: {text[:80]}...")
                        
                        # Save current channel and message count
                        temp_count = current_count
                        
                        if (join_channel_by_id(driver, DESTINATION_CHANNEL_ID) and 
                            send_message(driver, text)):
                            print("✅ Message forwarded successfully")
                        else:
                            print("❌ Forwarding failed")
                        
                        # Return to source and restore count
                        join_channel_by_id(driver, SOURCE_CHANNEL_ID)
                        last_message_count = temp_count
                    else:
                        last_message_count = current_count
                else:
                    last_message_count = current_count
            else:
                # Normal operation - no new messages
                if check_count % 20 == 0:
                    print(f"👀 Monitoring active (check #{check_count}, stable: {session_keeper.consecutive_stable_checks})")
            
            # 3. Adaptive waiting based on stability
            if session_keeper.consecutive_stable_checks > 10:
                wait_time = random.uniform(2, 4)  # Fast checks when stable
            else:
                wait_time = random.uniform(5, 8)  # Slower checks when unstable
            
            time.sleep(wait_time)
            
    except KeyboardInterrupt:
        print("🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
    finally:
        try:
            driver.quit()
            print("🔚 Session closed cleanly")
        except:
            pass

def main():
    print("🔐 Starting Preventive Session Management Bot")
    print(f"📅 Started at: {datetime.datetime.now()}")
    
    try:
        monitor_messages_with_prevention()
    except Exception as e:
        print(f"💥 Fatal error: {e}")
    finally:
        print(f"📅 Ended at: {datetime.datetime.now()}")

# ========= KEEP-ALIVE WEB ENDPOINT =========
from fastapi import FastAPI
import threading, uvicorn

app = FastAPI()

@app.get("/")
def home():
    return {"status": "alive", "message": "Session management bot is running 🌀"}

def run_web():
    uvicorn.run(app, host="0.0.0.0", port=10000)

# start the web server in a separate thread so it doesn’t block your bot
threading.Thread(target=run_web, daemon=True).start()

if __name__ == "__main__":
    main()
