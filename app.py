import requests
from bs4 import BeautifulSoup

# Optionally: Fetch the Discord webhook URL from GitHub Secrets
WEBHOOK_URL = "https://discord.com/api/webhooks/1342925652101304330/xxKBNz7qrURFTwlx27zeia4j7yviWRrLIx8p245c5s3jvTE2Tmblh1_fA74Fcq8oNMnK"

# Define the Vinted search URL (you can adjust the search criteria as needed)
VINTED_URL = 'https://www.vinted.com/catalog?order=newest_first&time=1740249466&search_text=ralph%20lauren&page=1'  # Example: Replace with your target search URL

# Function to send a message to Discord
def send_to_discord(item):
    payload = {
       "content": f"🆕 New item: {item['title']} - {item['link']} (💰 {item['price']})"
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        print(f"Successfully sent item to Discord: {item['title']}")
    else:
        print(f"Failed to send item to Discord, status code: {response.status_code}")

# Function to scrape Vinted
def scrape_vinted():
    print("Starting the scraping process...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Make a request to Vinted's search page
    response = requests.get(VINTED_URL, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to fetch Vinted page, status code: {response.status_code}")
        return
    
    # Parse the page with BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')

    # Example: Extract items (this is just a simple example, adjust according to Vinted's HTML structure)
    items = soup.find_all('a', class_='item_class')  # Adjust 'item_class' based on actual Vinted HTML

    for item in items:
        title = item.get_text(strip=True)
        link = item['href']
        price = item.find('span', class_='price_class').get_text(strip=True)  # Adjust 'price_class'
        
        # Send the item info to Discord
        send_to_discord({
            'title': title,
            'link': link,
            'price': price
        })

# Run the scraping function
if __name__ == "__main__":
    scrape_vinted()
