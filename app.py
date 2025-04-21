from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from bs4 import BeautifulSoup
import requests
from textblob import TextBlob
import requests
import numpy as np
from datetime import datetime, timedelta
from cachetools import TTLCache
import logging
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["https://sentidex.onrender.com"])

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://sentidex.onrender.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/')
def home():
    return render_template('index.html')

cache = TTLCache(maxsize=100, ttl=3600)
logger = logging.getLogger(__name__)

def get_yfinance_data(ticker):
    """Fetch stock data for the past 5 days using Yahoo Finance web scraping"""
    try:
        url = f"https://finance.yahoo.com/quote/{ticker}/history?p={ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        resp = requests.get(url, headers=headers)
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.find('table', {'class': 'table'})

        if not table:
            return None, "Could not find the table with stock data"

        rows = table.find('tbody').find_all('tr')
        stock_data = []
        close_prices = []
        dates = []

        # Counter to limit to 5 days
        days_collected = 0
        
        for row in rows:
            if days_collected >= 5:
                break
                
            columns = row.find_all('td')
            if len(columns) > 6:  # Make sure it's a data row (not dividend, split, etc.)
                date_text = columns[0].text.strip()
                close_price_text = columns[4].text.strip()
                
                try:
                    # Skip rows that don't contain price data (like dividends)
                    if not re.match(r'^\d+\.\d+$', close_price_text):
                        continue
                        
                    formatted_date = datetime.strptime(date_text, '%b %d, %Y').strftime('%Y-%m-%d')
                    dates.append(formatted_date)
                    close_prices.append(float(close_price_text))
                    days_collected += 1
                except ValueError as e:
                    print(f"Error parsing date {date_text}: {e}")

        if not close_prices:
            return None, "No valid price data found for the past 5 days"

        return {
            'ticker': ticker,
            'company_name': ticker,
            'currency': 'USD',
            'current_price': close_prices[0],  # Most recent price
            'price_data': {
                'dates': dates[:5],  # Ensure only 5 days
                'prices': close_prices[:5]  # Ensure only 5 days
            },
            'source': 'Yahoo Finance',
            'timestamp': datetime.now().isoformat()
        }, None

    except Exception as e:
        return None, f"Failed to fetch data: {str(e)}"



def calculate_predictions(ticker, current_price):
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Load the page
        url = f"https://finance.yahoo.com/quote/{ticker}"
        driver.get(url)
        
        # Wait for news section to load
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "section[data-testid='recent-news'] h3"))
            )
        except:
            print("Timed out waiting for news to load")
            return None
        
        # Wait an additional second for stability
        time.sleep(1)
        
        # Get the page source and parse with BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Find the news section and headlines
        recent_news = soup.find('section', {'data-testid': 'recent-news'})
        if not recent_news:
            print("Could not find recent news section")
            return None
            
        headlines = recent_news.find_all('h3', class_='clamp yf-82qtw3')
        if not headlines:
            print("No headlines found with specified class")
            return None
            
        # Process headlines and calculate sentiment
        sentiments = []
        for headline in headlines:
            text = headline.get_text().strip()
            try:
                sentiment = TextBlob(text).sentiment.polarity
                sentiments.append(sentiment)
            except Exception as e:
                print(f"Error analyzing sentiment: {e}")
                continue
        
        if not sentiments:
            return None
            
        # Calculate prediction
        average = sum(sentiments) / len(sentiments)
        normalized = max(-0.5, min(0.5, average / 2))
        predicted_price = current_price * (1 + normalized)
        
        return [{
            'type': 'Headline Sentiment Analysis',
            'price': round(predicted_price, 2),
            'confidence': 'low' if abs(normalized) > .4 else 'medium' if abs(normalized) > .2 else 'high' ,
            'num_headlines': len(headlines),
            'avg_sentiment': average,
            'sentiment': normalized
        }]
        
    finally:
        driver.quit()

@app.route('/search', methods=['POST', 'OPTIONS'])
def handle_search():
    data = request.get_json()
    ticker = data.get('ticker', '').upper().strip()

    if not ticker:
        return jsonify({'error': 'No ticker provided'}), 400

    if ticker in cache:
        return jsonify(cache[ticker])

    stock_data, error = get_yfinance_data(ticker)
    if error:
        return jsonify({
            'error': error,
            'ticker': ticker,
            'suggestion': 'Please try again later'
        }), 400
    
    stock_data['price_data']['dates'] = stock_data['price_data']['dates'][::-1]
    stock_data['price_data']['prices'] = stock_data['price_data']['prices'][::-1]

    predictions = calculate_predictions(ticker, stock_data['price_data']['prices'][-1])
    if predictions:
        stock_data['price_data']['predictions'] = predictions
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        stock_data['price_data']['dates'].append(tomorrow)
        stock_data['price_data']['prices'].append(predictions[0]['price'])

    cache[ticker] = stock_data
    return jsonify(stock_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

