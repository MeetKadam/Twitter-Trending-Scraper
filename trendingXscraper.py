#Note - PLEASE READ THE COMMENTS

from flask import Flask, render_template_string
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from pymongo import MongoClient
import time
import uuid
import datetime
import requests
from selenium.webdriver.common.proxy import Proxy, ProxyType

app = Flask(__name__)

# MongoDB setup
client = MongoClient("mongodb://localhost:27017/")  # Update according to your MongoDB URI 
db = client['twitter_scraper']
collection = db['trending_topics']

# HTML 
index_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Twitter(X) Scraper</title>
</head>
<body>
    <h1>Twitter Scraper</h1>
    <a href="/run-script">Click here to run the script.</a>
</body>
</html>
"""

results_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trending Topics</title>
</head>
<body>
    <p>These are the most happening topics as on {{ record['datetime'] }}</p>
    <ul>
        <li>{{ record['trend1'] }}</li>
        <li>{{ record['trend2'] }}</li>
        <li>{{ record['trend3'] }}</li>
        <li>{{ record['trend4'] }}</li>
        <li>{{ record['trend5'] }}</li>
    </ul>
    <p>The IP address used for this query was {{ record['ip_address'] }}.</p>
    <h2>JSON Extract:</h2>
    <p>{{ record }}</p>
    <a href="/">Click here to run the query again.</a>
</body>
</html>
"""

def run_selenium_script():
    """Runs the Selenium scraper and stores data in MongoDB using ProxyMesh."""
    
    options = webdriver.ChromeOptions()
    options.add_argument('--proxy-server=http://ID:PASS@us-ca.proxymesh.com:31280') # Insert your proxymesh username instead of 'ID' and your password instead of 'PASS'

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    
    try:
        driver.get("https://x.com/login")
        time.sleep(15)  # Adjust based on your internet speed

        # Example data - Replace with actual Twitter login details
        username = "your username or email"
        password = "your password"

        driver.find_element(By.XPATH, "//input[@name='text']").send_keys(username)
        driver.find_element(By.XPATH, "//span[text()='Next']").click()
        time.sleep(10)
        driver.find_element(By.XPATH, "//input[@name='password']").send_keys(password)
        driver.find_element(By.XPATH, "//span[text()='Log in']").click()
        time.sleep(20)

        # Fetch trending topics
        trending_topics = driver.find_elements(By.XPATH, "//*[contains(@aria-label, 'Timeline: Trending now')]//span")
        filtered_topics = set() 

        for topic in trending_topics:
            text = topic.text.strip()
        
            if (
                text
                and len(text) > 2
                and "what’s happening" not in text.lower()
                and "trending" not in text.lower()
                and "posts" not in text.lower()
                and "live" not in text.lower()
                and "show more" not in text.lower()
            ):
                filtered_topics.add(text)  # To ensure uniqueness


        filtered_topics = list(filtered_topics)

        unique_id = str(uuid.uuid4())
        end_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        ip_address = requests.get("https://api.ipify.org").text # Fetching IP address

        record = {
            "_id": unique_id,
            "trend1": filtered_topics[0] if len(filtered_topics) > 0 else "N/A",
            "trend2": filtered_topics[1] if len(filtered_topics) > 1 else "N/A",
            "trend3": filtered_topics[2] if len(filtered_topics) > 2 else "N/A",
            "trend4": filtered_topics[3] if len(filtered_topics) > 3 else "N/A",
            "trend5": filtered_topics[4] if len(filtered_topics) > 4 else "N/A",
            "datetime": end_time,
            "ip_address": ip_address,
        }

        # Inserting data into MongoDB
        collection.insert_one(record)
        return record

    finally:
        driver.quit()

@app.route('/')
def home():
    return render_template_string(index_template)

@app.route('/run-script')
def run_script():
    record = run_selenium_script()
    return render_template_string(results_template, record=record)

if __name__ == "__main__":
    app.run(debug=True)
