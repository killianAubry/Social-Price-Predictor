import praw
import random
from textblob import TextBlob
from InvestopediaApi import ita

reddit = praw.Reddit(
    client_id="zuleDiNXp9WmpcdbCHiQpw",
    client_secret="Sjqmys-vQ87jzvBefuykI8mLqO2t7A",
    user_agent="MyRedditApp/1.0 by timmothy"
)

investopedia_client = ita.Account("*******", "*****")

# Function to scrape popular comments from 5 random Reddit posts
def scrape_reddit_comments(subreddit="apple", num_posts=5):
    comments = []
    subreddit = reddit.subreddit(subreddit)

    # Search for posts from the past week
    posts = list(subreddit.search(
        query="",
        sort="hot",
        time_filter="week",
        limit=10  # Get up to 50 posts
    ))
    random_posts = random.sample(posts, min(num_posts, len(posts)))  # Select random posts

    for post in random_posts:
        post.comments.replace_more(limit=0)  # Load all comments
        for comment in post.comments.list():
            comments.append(comment.body)  # Collect comment text

    return comments

# Function to analyze sentiment
def analyze_sentiment(comments):
    sentiments = []
    for comment in comments:
        analysis = TextBlob(comment)
        sentiments.append(analysis.sentiment.polarity)  # Sentiment polarity: -1 (negative) to 1 (positive)
    return sentiments

# Function to decide trades based on sentiment
def execute_trade(sentiments, stock_symbol="AAPL", quantity=10):
    avg_sentiment = sum(sentiments) / len(sentiments)
    if avg_sentiment > 0.1:  # Positive sentiment threshold
        print(f"Positive sentiment detected ({avg_sentiment}). Buying {quantity} shares of {stock_symbol}.")
        investopedia_client.trade(stock_symbol, ita.Action.buy, quantity)
    elif avg_sentiment < -0.1:  # Negative sentiment threshold
        print(f"Negative sentiment detected ({avg_sentiment}). Selling {quantity} shares of {stock_symbol}.")
        investopedia_client.trade(stock_symbol, ita.Action.sell, quantity)
    else:
        print(f"Neutral sentiment detected ({avg_sentiment}). No action taken.")

# Main function to coordinate the process
def main():
    # Step 1: Scrape Reddit
    print("Scraping Reddit for comments...")
    comments = scrape_reddit_comments()
    print(f"Collected {len(comments)} comments.")

    # Step 2: Perform sentiment analysis
    print("Analyzing sentiment...")
    sentiments = analyze_sentiment(comments)

    # Step 3: Execute trade based on sentiment
    print("Executing trade based on sentiment...")
    execute_trade(sentiments, stock_symbol="AAPL", quantity=10)

if __name__ == "__main__":
    main()