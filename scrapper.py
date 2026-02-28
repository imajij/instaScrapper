"""
instagram_followees_scraper_v3.py

Enhanced version with aggressive modal scrolling and better Instagram handling

Requirements:
  pip install selenium webdriver-manager pandas

Key improvements:
  - Aggressive modal scrolling with multiple strategies
  - Better detection of modal elements
  - Handles Instagram's infinite scroll properly
  - Extracts all fields: Name, Followers, Posts, Bio, Email, Verified, Links
"""
import time
import random
import csv
import re
import os
import json
from pathlib import Path
from typing import List, Dict, Optional

import platform

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementClickInterceptedException,
    StaleElementReferenceException, WebDriverException
)
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# --------- CONFIG ----------
INSTAGRAM_USERNAME = "your_username"
INSTAGRAM_PASSWORD = "your_passwordd"
TARGET_ACCOUNT = "ashneer.grover"
OUTPUT_CSV = f"{TARGET_ACCOUNT}_followees_detailed.csv"
CHECKPOINT_FILE = f"{TARGET_ACCOUNT}_checkpoint.json"

HEADLESS = False  # Set to False for debugging modal issues
BATCH_SIZE = 25
DELAY_RANGE = (3.0, 6.0)
SCROLL_PAUSE = 2.0  # Increased - time between scrolls (try 3.0 if still having issues)
MAX_FOLLOWEES_TO_COLLECT = None  # Set to a number like 50 for testing
SAVE_FREQUENCY = 10

# Advanced scrolling settings
SCROLL_MAX_NO_CHANGE = 25  # How many scroll attempts with no new usernames before stopping
SCROLL_PATIENCE_MULTIPLIER = 1.5  # Increase this to 2.0 or 3.0 for even more patience

# Patterns
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
URL_PATTERN = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

# ---------- HELPER FUNCTIONS ----------

def rand_sleep(a=None, b=None):
    if a is None:
        a, b = DELAY_RANGE
    t = random.uniform(a, b)
    time.sleep(t)

def save_checkpoint(usernames: List[str], processed: List[str]):
    checkpoint = {
        "usernames": usernames,
        "processed": processed,
        "timestamp": time.time()
    }
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f)
    print(f"✓ Checkpoint saved ({len(processed)}/{len(usernames)} processed)")

def load_checkpoint() -> Optional[Dict]:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r') as f:
            return json.load(f)
    return None

def _find_browser():
    """
    Scan known OS-specific paths for Google Chrome and Chromium.
    Returns (binary_path: str | None, is_chromium: bool).
    Order matters — Google Chrome is preferred over Chromium where both exist.
    """
    OS = platform.system()
    if OS == "Darwin":
        candidates = [
            ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", False),
            ("/Applications/Chromium.app/Contents/MacOS/Chromium", True),
        ]
    elif OS == "Linux":
        candidates = [
            ("/usr/bin/google-chrome", False),
            ("/usr/bin/google-chrome-stable", False),
            ("/opt/google/chrome/google-chrome", False),
            ("/usr/bin/chromium", True),
            ("/usr/bin/chromium-browser", True),
            ("/usr/sbin/chromium", True),
            ("/snap/bin/chromium", True),
        ]
    else:  # Windows
        candidates = [
            (r"C:\Program Files\Google\Chrome\Application\chrome.exe", False),
            (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", False),
        ]
    for path, is_chromium in candidates:
        if os.path.exists(path):
            return path, is_chromium
    return None, False


def start_driver(headless=HEADLESS):
    print("Starting driver...")
    IS_MAC = platform.system() == "Darwin"
    IS_LINUX = platform.system() == "Linux"

    options = webdriver.ChromeOptions()

    # Auto-detect which browser (Chrome vs Chromium) and where it lives
    browser_binary, is_chromium = _find_browser()
    if browser_binary:
        print(f"  Browser: {'Chromium' if is_chromium else 'Google Chrome'} → {browser_binary}")
        options.binary_location = browser_binary
    else:
        print("  Warning: could not locate Chrome/Chromium binary; letting Selenium try PATH")

    if headless:
        options.add_argument("--headless=new")
        if not IS_MAC:  # --disable-gpu can cause rendering issues on macOS
            options.add_argument("--disable-gpu")

    # Linux/Docker-specific flags — skip on macOS where they cause instability
    if not IS_MAC:
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-notifications")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--lang=en-US")
    options.add_argument("--window-size=1920,1080")

    # Match user-agent to the actual OS so Instagram renders the expected layout
    if IS_MAC:
        user_agent = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36")
    else:
        user_agent = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/120.0.0.0 Safari/537.36")
    options.add_argument(f"user-agent={user_agent}")

    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_experimental_option("prefs", {
        "profile.default_content_setting_values.notifications": 2
    })

    # Use webdriver-manager to fetch the chromedriver that matches the installed
    # browser version.  When the browser is Chromium we must pass
    # chrome_type=ChromeType.CHROMIUM, otherwise wdm downloads a Chrome driver
    # (capped at v114) that is incompatible with newer Chromium builds.
    try:
        from webdriver_manager.core.os_manager import ChromeType
        chrome_type = ChromeType.CHROMIUM if is_chromium else ChromeType.GOOGLE
        service = ChromeService(ChromeDriverManager(chrome_type=chrome_type).install())
    except Exception as e:
        print(f"Warning: webdriver-manager failed ({e}), falling back to PATH chromedriver")
        service = ChromeService()

    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    return driver

def login_instagram(driver, username, password):
    try:
        print("Navigating to Instagram login...")
        driver.get("https://www.instagram.com/accounts/login/")
        rand_sleep(3, 5)
        
        # Accept cookies
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Allow') or contains(text(), 'Accept')]"))
            )
            cookie_button.click()
            rand_sleep(1, 2)
        except:
            pass
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.NAME, "username"))
        )
        
        username_input = driver.find_element(By.NAME, "username")
        password_input = driver.find_element(By.NAME, "password")
        
        # Type slowly
        for char in username:
            username_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        
        rand_sleep(0.5, 1)
        
        for char in password:
            password_input.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        
        rand_sleep(1, 2)
        password_input.send_keys(Keys.RETURN)
        rand_sleep(5, 8)
        
        if "/accounts/login" not in driver.current_url:
            print("✓ Login successful!")
            
            # Handle dialogs
            try:
                not_now = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not now') or contains(text(), 'Not Now')]"))
                )
                not_now.click()
                rand_sleep(1, 2)
            except:
                pass
            
            try:
                not_now = WebDriverWait(driver, 8).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')]"))
                )
                not_now.click()
                rand_sleep(1, 2)
            except:
                pass
            
            return True
        else:
            print("✗ Login failed")
            driver.save_screenshot("login_failed.png")
            return False
            
    except Exception as e:
        print(f"✗ Login error: {e}")
        driver.save_screenshot("login_error.png")
        return False

def open_following_modal(driver, target_username):
    profile_url = f"https://www.instagram.com/{target_username}/"
    print(f"Opening profile: {profile_url}")
    
    try:
        driver.get(profile_url)
        rand_sleep(5, 8)
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "header"))
        )
        
        # Check if private
        try:
            driver.find_element(By.XPATH, "//*[contains(text(), 'This account is private') or contains(text(), 'This Account is Private')]")
            print("✗ Account is private!")
            return None
        except:
            pass
        
        # Find following link - try multiple methods
        following_clicked = False
        
        # Method 1: Direct href
        try:
            following_btn = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(@href, '/{target_username}/following')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", following_btn)
            rand_sleep(0.5, 1)
            driver.execute_script("arguments[0].click();", following_btn)
            following_clicked = True
            print("✓ Clicked following (method 1)")
        except:
            pass
        
        # Method 2: Search all links
        if not following_clicked:
            try:
                links = driver.find_elements(By.XPATH, "//header//a")
                for link in links:
                    href = link.get_attribute('href') or ""
                    if 'following' in href.lower():
                        driver.execute_script("arguments[0].click();", link)
                        following_clicked = True
                        print("✓ Clicked following (method 2)")
                        break
            except:
                pass
        
        # Method 3: Click by text
        if not following_clicked:
            try:
                following_btn = driver.find_element(By.XPATH, "//a[contains(text(), 'following') or contains(text(), 'Following')]")
                driver.execute_script("arguments[0].click();", following_btn)
                following_clicked = True
                print("✓ Clicked following (method 3)")
            except:
                pass
        
        if not following_clicked:
            print("✗ Could not click following button")
            driver.save_screenshot("following_not_found.png")
            return None
        
        rand_sleep(3, 5)
        
        # Wait for modal
        modal = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='dialog']"))
        )
        print("✓ Following modal opened")
        
        # Give modal time to initialize
        rand_sleep(2, 3)
        
        return modal
        
    except Exception as e:
        print(f"✗ Error opening modal: {e}")
        driver.save_screenshot("modal_error.png")
        return None

def collect_usernames_from_modal(driver, modal, max_count=None):
    """
    Aggressively scroll the modal and collect ALL usernames.
    Uses multiple scrolling strategies with extended patience.
    """
    usernames = set()
    prev_count = 0
    no_change_count = 0
    scroll_attempt = 0
    max_no_change = int(SCROLL_MAX_NO_CHANGE * SCROLL_PATIENCE_MULTIPLIER)
    consecutive_failures = 0
    last_scroll_height = 0
    
    print("Collecting usernames from modal...")
    print("This may take a while - please be patient...")
    
    # Find the scrollable div inside the modal
    scrollable_div = None
    try:
        possible_divs = modal.find_elements(By.XPATH, ".//div")
        for div in possible_divs:
            overflow = driver.execute_script(
                "return window.getComputedStyle(arguments[0]).overflowY;", div
            )
            if overflow in ['scroll', 'auto']:
                scrollable_div = div
                print("✓ Found scrollable container")
                break
    except:
        pass
    
    if not scrollable_div:
        scrollable_div = modal
        print("Using modal as scrollable container")
    
    # Get initial scroll height
    try:
        last_scroll_height = driver.execute_script(
            "return arguments[0].scrollHeight;", scrollable_div
        )
    except:
        pass
    
    while True:
        scroll_attempt += 1
        
        # Extract usernames from current view
        try:
            links = scrollable_div.find_elements(By.XPATH, ".//a[contains(@href, '/')]")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if href:
                        match = re.match(r"https?://(www\.)?instagram\.com/([^/?#]+)/?", href)
                        if match:
                            username = match.group(2).strip("/")
                            excluded = ['explore', 'p', 'reel', 'reels', 'tv', 'stories', 
                                      'direct', 'accounts', 'about', 'legal', 'help']
                            if (username.lower() not in excluded and
                                username.lower() != TARGET_ACCOUNT.lower() and
                                len(username) > 1 and
                                not username.startswith('hashtag')):
                                usernames.add(username)
                except (StaleElementReferenceException, AttributeError):
                    continue
        except StaleElementReferenceException:
            continue
        
        current_count = len(usernames)
        
        # Check if scroll height changed (indicates new content loaded)
        try:
            current_scroll_height = driver.execute_script(
                "return arguments[0].scrollHeight;", scrollable_div
            )
            if current_scroll_height > last_scroll_height:
                consecutive_failures = 0
                last_scroll_height = current_scroll_height
            else:
                consecutive_failures += 1
        except:
            pass
        
        # Log progress
        if current_count > prev_count:
            print(f"  📊 Collected {current_count} usernames... (scroll #{scroll_attempt})")
            no_change_count = 0
            consecutive_failures = 0
            prev_count = current_count
        else:
            no_change_count += 1
            if no_change_count % 5 == 0:
                print(f"  ⏳ Still at {current_count} usernames... (no change for {no_change_count} attempts)")
        
        # Check stopping conditions
        if max_count and current_count >= max_count:
            print(f"✓ Reached target of {max_count} usernames")
            break
        
        # More conservative stopping - need both conditions
        if no_change_count >= max_no_change and consecutive_failures >= 10:
            print(f"✓ No new content after {max_no_change} attempts - stopping")
            break
        
        # SUPER AGGRESSIVE SCROLLING with multiple strategies
        
        # Strategy 1: Scroll to absolute bottom
        try:
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                scrollable_div
            )
        except:
            pass
        
        time.sleep(SCROLL_PAUSE)
        
        # Strategy 2: Scroll by large fixed amount
        try:
            current_scroll = driver.execute_script(
                "return arguments[0].scrollTop;", scrollable_div
            )
            driver.execute_script(
                "arguments[0].scrollTop = arguments[1] + 500;", 
                scrollable_div, current_scroll
            )
        except:
            pass
        
        time.sleep(0.5)
        
        # Strategy 3: Keyboard scrolling with ActionChains
        try:
            actions = ActionChains(driver)
            actions.move_to_element(scrollable_div).perform()
            for _ in range(3):
                scrollable_div.send_keys(Keys.PAGE_DOWN)
                time.sleep(0.2)
        except:
            pass
        
        time.sleep(0.3)
        
        # Strategy 4: Scroll to last visible element
        try:
            all_items = scrollable_div.find_elements(By.XPATH, ".//a")
            if len(all_items) > 5:
                last_item = all_items[-2]
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior: 'smooth', block: 'end'});", 
                    last_item
                )
        except:
            pass
        
        time.sleep(0.5)
        
        # Strategy 5: Mouse wheel simulation
        try:
            driver.execute_script(
                "arguments[0].dispatchEvent(new WheelEvent('wheel', {deltaY: 1000}));",
                scrollable_div
            )
        except:
            pass
        
        time.sleep(SCROLL_PAUSE + random.uniform(0.3, 1.0))
        
        # Every 10 scrolls - MEGA AGGRESSIVE burst
        if scroll_attempt % 10 == 0:
            print(f"  💪 Aggressive scroll burst at attempt {scroll_attempt}...")
            try:
                for i in range(5):
                    driver.execute_script(
                        "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                        scrollable_div
                    )
                    time.sleep(0.3)
                    
                    # Also try scrolling by pixels
                    driver.execute_script(
                        "arguments[0].scrollBy(0, 1000);", 
                        scrollable_div
                    )
                    time.sleep(0.3)
            except:
                pass
        
        # Every 20 scrolls - try to "wake up" the modal
        if scroll_attempt % 20 == 0:
            print(f"  🔄 Refreshing modal at attempt {scroll_attempt}...")
            try:
                # Click somewhere safe in modal to trigger re-render
                driver.execute_script("arguments[0].click();", scrollable_div)
                time.sleep(0.5)
                
                # Scroll to top then back to bottom
                driver.execute_script("arguments[0].scrollTop = 0;", scrollable_div)
                time.sleep(0.5)
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                    scrollable_div
                )
                time.sleep(1)
            except:
                pass
    
    result = sorted(list(usernames))
    print(f"\n✓ Final count: {len(result)} unique usernames collected")
    
    # Save usernames to file
    with open(f"{TARGET_ACCOUNT}_usernames.txt", "w") as f:
        f.write("\n".join(result))
    print(f"✓ Usernames saved to {TARGET_ACCOUNT}_usernames.txt")
    
    return result

def extract_email(text):
    if not text:
        return ""
    matches = EMAIL_PATTERN.findall(text)
    return matches[0] if matches else ""

def extract_external_links(driver):
    links = []
    try:
        link_elements = driver.find_elements(By.XPATH, "//header//a[starts-with(@href, 'http') and not(contains(@href, 'instagram.com'))]")
        for elem in link_elements:
            try:
                href = elem.get_attribute('href')
                if href and 'instagram.com' not in href:
                    links.append(href)
            except:
                continue
    except:
        pass
    
    return ", ".join(links) if links else ""

def check_verified(driver):
    try:
        driver.find_element(By.XPATH, "//header//*[name()='svg' and @aria-label='Verified']")
        return "Yes"
    except:
        try:
            driver.find_element(By.XPATH, "//header//*[contains(@aria-label, 'Verified') or contains(@title, 'Verified')]")
            return "Yes"
        except:
            return "No"

def parse_stat_number(text):
    if not text:
        return None
    
    text = str(text).strip().upper().replace(',', '')
    
    multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}
    
    for suffix, multiplier in multipliers.items():
        if suffix in text:
            try:
                num = float(text.replace(suffix, ''))
                return str(int(num * multiplier))
            except:
                return text
    
    try:
        return str(int(float(text)))
    except:
        return text

def scrape_profile(driver, username):
    url = f"https://www.instagram.com/{username}/"
    
    data = {
        "username": username,
        "name": "",
        "followers": "",
        "posts": "",
        "bio": "",
        "email": "",
        "verified": "No",
        "profile_link": url,
        "bio_links": ""
    }
    
    try:
        driver.get(url)
        rand_sleep(3, 5)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "header"))
        )
        
        # PRIORITY 1: Try meta tag first (most reliable)
        try:
            meta = driver.find_element(By.XPATH, "//meta[@property='og:description']")
            content = meta.get_attribute("content")
            
            # Pattern: "X Followers, Y Following, Z Posts - See Instagram..."
            followers_match = re.search(r'([\d,\.]+[KMB]?)\s+Followers', content, re.IGNORECASE)
            posts_match = re.search(r'([\d,\.]+[KMB]?)\s+Posts', content, re.IGNORECASE)
            
            if followers_match:
                data["followers"] = parse_stat_number(followers_match.group(1))
                print(f"    📊 Followers from meta: {data['followers']}")
            if posts_match:
                data["posts"] = parse_stat_number(posts_match.group(1))
                print(f"    📊 Posts from meta: {data['posts']}")
        except Exception as e:
            print(f"    ⚠️  Meta tag method failed: {e}")
        
        # PRIORITY 2: Parse stats from header list items
        if not data["followers"] or not data["posts"]:
            try:
                # Get all list items in header
                stat_items = driver.find_elements(By.XPATH, "//header//ul/li")
                
                for item in stat_items:
                    try:
                        item_text = item.text.strip().lower()
                        
                        # Split by newlines and spaces
                        parts = re.split(r'[\n\s]+', item_text)
                        
                        # Look for pattern: number followed by label
                        for i, part in enumerate(parts):
                            # Check if this part is a number
                            if re.match(r'^[\d,\.]+[kmb]?$', part, re.IGNORECASE):
                                number = part
                                # Check the next part for label
                                if i + 1 < len(parts):
                                    label = parts[i + 1].lower()

                                    if 'post' in label:
                                        data["posts"] = parse_stat_number(number)
                                        print(f"    📊 Posts from list: {data['posts']}")
                                    elif 'follower' in label:
                                        data["followers"] = parse_stat_number(number)
                                        print(f"    📊 Followers from list: {data['followers']}")
                    except:
                        continue
            except Exception as e:
                print(f"    ⚠️  List parsing failed: {e}")

        # PRIORITY 3: Try direct link-based approach
        if not data["followers"]:
            try:
                # Followers link contains '/followers/'
                followers_link = driver.find_element(By.XPATH, "//a[contains(@href, '/followers/')]")
                followers_text = followers_link.text.strip()
                
                # Extract number from text like "1,234 followers" or just "1234"
                number_match = re.search(r'([\d,\.]+[KMB]?)', followers_text, re.IGNORECASE)
                if number_match:
                    data["followers"] = parse_stat_number(number_match.group(1))
                    print(f"    📊 Followers from link: {data['followers']}")
            except:
                pass
        
        if not data["posts"]:
            try:
                # Find element that shows post count (usually first in the list)
                post_elements = driver.find_elements(By.XPATH, "//header//ul/li[1]//span")
                for elem in post_elements:
                    text = elem.text.strip()
                    # Check if it's a number
                    if re.match(r'^[\d,\.]+[KMB]?$', text, re.IGNORECASE):
                        data["posts"] = parse_stat_number(text)
                        print(f"    📊 Posts from first li: {data['posts']}")
                        break
            except:
                pass
        
        # Get name (full name)
        name_selectors = [
            "//header//section//div//span[not(contains(@class, 'html-span'))]",
            "//header//span[contains(@class, 'x1lliihq')]",
            "//header//h2//span",
            "//header//h1",
        ]
        
        for selector in name_selectors:
            try:
                name_elem = driver.find_element(By.XPATH, selector)
                name = name_elem.text.strip()
                # Make sure it's not the username and not a stat
                if (name and 
                    name != username and 
                    len(name) > 0 and 
                    not re.match(r'^[\d,\.]+[KMB]?$', name, re.IGNORECASE) and
                    'post' not in name.lower() and
                    'follow' not in name.lower()):
                    data["name"] = name
                    print(f"    👤 Name: {data['name']}")
                    break
            except:
                continue
        
        # Get bio
        bio_selectors = [
            "//header//h1/following-sibling::div//span[not(contains(text(), 'Follow'))]",
            "//header//section//div//span[string-length(text()) > 10]",
            "//main//header//div//span[string-length(text()) > 10]",
        ]
        
        for selector in bio_selectors:
            try:
                bio_elems = driver.find_elements(By.XPATH, selector)
                for bio_elem in bio_elems:
                    bio = bio_elem.text.strip()
                    # Make sure it's not stats or username
                    if (bio and 
                        len(bio) > 5 and 
                        bio != username and
                        bio != data.get("name", "") and
                        not re.match(r'^[\d,\.]+[KMB]?\s+(post|follower|following)', bio, re.IGNORECASE)):
                        data["bio"] = bio
                        print(f"    📝 Bio: {bio[:50]}...")
                        break
                if data["bio"]:
                    break
            except:
                continue
        
        # Extract email from bio
        if data["bio"]:
            email = extract_email(data["bio"])
            if email:
                data["email"] = email
                print(f"    📧 Email: {email}")
        
        # Check if verified
        data["verified"] = check_verified(driver)
        if data["verified"] == "Yes":
            print(f"    ✓ Verified account")
        
        # Get external links from bio
        bio_links = extract_external_links(driver)
        if bio_links:
            data["bio_links"] = bio_links
            print(f"    🔗 Links: {bio_links}")
        
        print(f"  ✓ {username}: {data['name']} | Followers: {data['followers']} | Posts: {data['posts']}")
        return data
        
    except Exception as e:
        print(f"  ✗ Error scraping {username}: {e}")
        import traceback
        traceback.print_exc()
        return data

def save_results(results, filename):
    if not results:
        print("No results to save")
        return
    
    df = pd.DataFrame(results)
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"✓ Saved {len(df)} profiles to {filename}")

# ---------- MAIN ----------

def main():
    driver = None
    results = []
    processed_usernames = []
    
    try:
        checkpoint = load_checkpoint()
        if checkpoint:
            print(f"Found checkpoint from {time.ctime(checkpoint['timestamp'])}")
            response = input("Resume from checkpoint? (y/n): ").lower()
            if response == 'y':
                usernames_to_scrape = checkpoint['usernames']
                processed_usernames = checkpoint['processed']
                print(f"Resuming: {len(processed_usernames)}/{len(usernames_to_scrape)} already processed")
                
                if os.path.exists(OUTPUT_CSV):
                    existing_df = pd.read_csv(OUTPUT_CSV)
                    results = existing_df.to_dict('records')
                
                driver = start_driver()
                if not login_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
                    return
                
                usernames_to_scrape = [u for u in usernames_to_scrape if u not in processed_usernames]
                
            else:
                checkpoint = None
        
        if not checkpoint:
            driver = start_driver()
            
            if not login_instagram(driver, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD):
                print("Exiting due to login failure")
                return
            
            modal = open_following_modal(driver, TARGET_ACCOUNT)
            if not modal:
                print("Exiting: Could not open following modal")
                return
            
            usernames_to_scrape = collect_usernames_from_modal(
                driver, modal, max_count=MAX_FOLLOWEES_TO_COLLECT
            )
            
            if not usernames_to_scrape:
                print("No usernames collected")
                return
            
            # Close modal
            try:
                driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                rand_sleep(1, 2)
            except:
                pass
        
        # Scrape profiles
        total = len(usernames_to_scrape)
        print(f"\n{'='*50}")
        print(f"Starting to scrape {total} profiles...")
        print(f"{'='*50}\n")
        
        for i, username in enumerate(usernames_to_scrape, 1):
            print(f"[{i}/{total}] Scraping {username}...")
            
            try:
                profile_data = scrape_profile(driver, username)
                if profile_data:
                    results.append(profile_data)
                    processed_usernames.append(username)
                
                if i % SAVE_FREQUENCY == 0:
                    save_results(results, OUTPUT_CSV)
                    if not checkpoint:
                        checkpoint = {'usernames': usernames_to_scrape}
                    save_checkpoint(
                        checkpoint['usernames'],
                        processed_usernames
                    )
                
                rand_sleep()
                
            except Exception as e:
                print(f"  ✗ Exception for {username}: {e}")
                continue
        
        save_results(results, OUTPUT_CSV)
        
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            print("✓ Checkpoint cleaned up")
        
        print(f"\n{'='*50}")
        print(f"COMPLETED! Scraped {len(results)} profiles")
        print(f"Results saved to: {OUTPUT_CSV}")
        print(f"{'='*50}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user!")
        save_results(results, OUTPUT_CSV)
        if 'usernames_to_scrape' in locals():
            if not checkpoint:
                checkpoint = {'usernames': usernames_to_scrape}
            save_checkpoint(checkpoint['usernames'], processed_usernames)
        
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        save_results(results, OUTPUT_CSV)
        
    finally:
        if driver:
            driver.quit()
            print("Driver closed")

if __name__ == "__main__":
    main()