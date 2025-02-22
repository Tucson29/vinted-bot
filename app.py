import requests
import os
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', "https://discord.com/api/webhooks/1342925652101304330/xxKBNz7qrURFTwlx27zeia4j7yviWRrLIx8p245c5s3jvTE2Tmblh1_fA74Fcq8oNMnK")
VINTED_API_URL = "https://www.vinted.com/api/v2/catalog/items?order=newest_first&time=1740254213&search_text=ralph%20lauren&page=1"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

COOKIE_FILE = "vinted_cookies.json"

def get_cookies():
    """Open Vinted with Selenium, log in, and save cookies."""
    print("🔑 Logging into Vinted to get cookies...")
    
    options = Options()
    options.headless = True  # Runs in background (no window)
    
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
        item_data = {
            "title": item["title"],
            "price": item["total_item_price"]["amount"],
            "url": f"https://www.vinted.com/items/{item['id']}"
        }
        send_to_discord(item_data)

def send_to_discord(item):
    payload = {
        "content": f"🆕 **{item['title']}**\n💰 {item['price']}€\n🔗 [View Item]({item['url']})"
    }
    response = requests.post(WEBHOOK_URL, json=payload)

    if response.status_code == 204:
        print(f"✅ Sent to Discord: {item['title']}")
    else:
        print(f"❌ Failed to send to Discord. Status: {response.status_code}, Response: {response.text}")

if __name__ == "__main__":
    scrape_vinted()
