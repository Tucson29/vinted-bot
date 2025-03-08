import requests
import os
import json
import tempfile
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time

CACHE_FILE = "exchange_rate_cache.json"
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
VINTED_API_URL = "https://www.vinted.hu/api/v2/catalog/items?order=newest_first&time=1740254213&search_text=ralph%20lauren&page=1&location=Budapest"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}

COOKIE_FILE = "vinted_cookies.json"

def get_cookies():
    """Open Vinted with Selenium, log in, and save cookies."""
    print("🔑 Logging into Vinted to get cookies...")
    
    # Create a temporary directory to store user data
    user_data_dir = tempfile.mkdtemp()

    options = Options()
    #options.headless = True  # Runs in background (no window)
    #options.add_argument(f"--user-data-dir={user_data_dir}")  # Use the unique directory for session
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # REMOVE: options.add_argument("--user-data-dir=...")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://www.vinted.com")

    
    cookies = driver.get_cookies()
    driver.quit()

    with open(COOKIE_FILE, "w") as file:
        json.dump(cookies, file)
    
    print("✅ Cookies saved!")

def load_cookies():
    """Load saved cookies."""
    if not os.path.exists(COOKIE_FILE):
        get_cookies()

    with open(COOKIE_FILE, "r") as file:
        cookies = json.load(file)
    
    return "; ".join([f"{c['name']}={c['value']}" for c in cookies])

def load_cache():
    """Load exchange rate cache from the cache file"""
    try:
        with open(CACHE_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return a default empty cache if file doesn't exist or is corrupt
        return {"rate": None, "timestamp": None}

def save_cache(rate, timestamp):
    """Save exchange rate and timestamp to the cache file"""
    with open(CACHE_FILE, 'w') as file:
        json.dump({"rate": rate, "timestamp": timestamp}, file)

def get_exchange_rate():
    # Load the cached rate
    exchange_rate_cache = load_cache()

    # Check if we already have a cached rate
    if exchange_rate_cache["rate"] and exchange_rate_cache["timestamp"]:
        # If the cached rate is less than 6 hours old, return the cached rate
        if datetime.now() - datetime.fromisoformat(exchange_rate_cache["timestamp"]) < timedelta(hours=10):
            print("Using cached exchange rate.")
            return exchange_rate_cache["rate"]
    
    print("Fetching new exchange rate...")
    # Get a new exchange rate from your API (for example, using requests to a URL)
    api_key = "4f370c8a17d76e3425f95fea242aba7c"  # Replace with your API key
    url = f"https://data.fixer.io/api/latest?access_key={api_key}&symbols=HUF,USD"  # Example API URL
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Let's assume you want USD to HUF
        usd_to_huf_rate = data['rates']['HUF']
        
        # Update the cache and save it to the file
        save_cache(usd_to_huf_rate, datetime.now().isoformat())
        return usd_to_huf_rate
    else:
        print(f"Error fetching exchange rate: {response.status_code}")
        return None

# Function to convert USD to HUF
def convert_usd_to_huf(usd_price):
    rate = get_exchange_rate()
    if rate:
        huf_price = float(usd_price) * rate
        return round(huf_price, 2)  # Round to 2 decimal places
    return None

def scrape_vinted():
    """Scrape Vinted API with saved cookies."""
    HEADERS["Cookie"] = load_cookies()

    print("🔎 Scraping Vinted API...")
    response = requests.get(VINTED_API_URL, headers=HEADERS)
    
    if response.status_code == 401:  # If authentication fails
        print("⚠️ Authentication failed! Refreshing cookies...")
        get_cookies()  # Refresh cookies
        return scrape_vinted()  # Retry

    if response.status_code != 200:
        print(f"❌ Failed to fetch Vinted API. Status code: {response.status_code}")
        return

    data = response.json()
    items = data.get("items", [])

    if not items:
        print("⚠️ No new items found.")
        return

    for item in items[:2]:
        print(item)
        item_data = {
            "title": item["title"],
            "price": round(float(item["total_item_price"]["amount"])),
            "currency_code": item["total_item_price"]["currency_code"],
            "url": f"https://www.vinted.com/items/{item['id']}",
            "photo": item["photo"]["url"],
            "size": item["size_title"]
            
        }
        send_to_discord(item_data)

def send_to_discord(item):
    #payload
    embed = {
        "embeds": [
            {
                "title": item['title'],
                "description": "✨New Raplh Lauren clothing!",
                "color": 0x00FFFF,  # Cyan color
                "url": item['url'],
                "fields": [
                    {
                        "name": f"💰 Price: {item['price']} {item['currency_code']}",
                        "value": "",
                        "inline": False
                    },
                    {
                        "name": f"📏 Size: {item['size']}",
                        "value": "",
                        "inline": False
                    }
                ],
                "image": {
                    "url": item['photo']  # Image URL for the item
                }
            }
        ]
    }


    response = requests.post(WEBHOOK_URL, data=json.dumps(embed), headers={"Content-Type": "application/json"})

    embed = ""
    if response.status_code == 204:
        print(f"✅ Sent to Discord: {item['title']}")
    else:
        print(f"❌ Failed to send to Discord. Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    for i in range(5):
        scrape_vinted()
        time.sleep(60)
