import praw
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
#testing

# Replace with your own Reddit credentials
reddit = praw.Reddit(
    client_id="zuleDiNXp9WmpcdbCHiQpw",
    client_secret="Sjqmys-vQ87jzvBefuykI8mLqO2t7A",
    user_agent="MyRedditApp/1.0 by timmothy"
)

# Specify the subreddit you want to scrape
subreddit = reddit.subreddit("teslainvestorsclub")

# Get the top posts from the past 14 days
posts = subreddit.top(time_filter="week", limit=None)

# Initialize a list to store comments and sentiment scores
comments = []
sentiment_scores = []

# Iterate through each post and extract comments
for post in posts:
    # Get the comments for the post
    post_comments = post.comments.list()

    # Iterate through each comment and extract text
    for comment in post_comments:
        # Check if the comment is a top-level comment (not a reply)
        if comment.parent_id == post.id:
            comments.append(comment.body)
print(comments)
# Perform sentiment analysis on each comment
sid = SentimentIntensityAnalyzer()
for comment in comments:
    sentiment_score = sid.polarity_scores(comment)['compound']
    sentiment_scores.append(sentiment_score)

# Calculate the average sentiment score
average_sentiment = sum(sentiment_scores) / len(sentiment_scores)

print("Average sentiment score:", average_sentiment)