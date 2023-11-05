from flask import Flask, request, jsonify
from gnews import GNews
from dotenv import load_dotenv
import openai
import os
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
from newspaper import Article
import feedparser
import tweepy

load_dotenv()
app = Flask(__name__)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/get_articles_by_quarter', methods=['GET'])
def get_articles_by_quarter():
    company_name = request.args.get('company_name', default='', type=str)
    today = datetime.now()
    interval_start = today - relativedelta(years=1, days=1)
    interval_end = interval_start + relativedelta(months=3)
    quarter_to_articles = []

    while interval_end < today:
        google_news = GNews(language='en', country='US', start_date=interval_start, end_date=interval_end, max_results=10)
        interval_articles = google_news.get_news(f'"{company_name}" news')
        quarter_to_articles.append(interval_articles)
        interval_start += relativedelta(months=3)
        interval_end += relativedelta(months=3)
    
    print(len(quarter_to_articles), file=sys.stderr)
    return jsonify(quarter_to_articles)

@app.route('/get_tweets_by_quarter', methods=['GET'])
def get_tweets_by_quarter():
    company_name = request.args.get('company_name', default='', type=str)
    today = datetime.now()
    interval_start = today - relativedelta(years=1, days=1)
    interval_end = interval_start + relativedelta(months=3)
    tweets_to_articles = []
    auth = tweepy.OAuth2BearerHandler("AAAAAAAAAAAAAAAAAAAAALd1qwEAAAAAA%2FPDm8%2F7vZteOLR3QSQTXxGX1FE%3DFZG0CnEgoocsmFHjmgkTUpyyBQmfKEYAY4PdEhccXjJh253gOP")
    api = tweepy.API(auth)

    while interval_end < today:
        #google_news = GNews(language='en', country='US', start_date=interval_start, end_date=interval_end, max_results=10)
        #interval_articles = google_news.get_news(f'"{company_name}" news')
        
        
        interval_articles = api.search_tweets(q = )
        tweets_to_articles.append(interval_articles)
        interval_start += relativedelta(months=3)
        interval_end += relativedelta(months=3)
    
    print(len(tweets_to_articles), file=sys.stderr)
    return jsonify(tweets_to_articles)

@app.route('/sentiment_analysis', methods=['POST'])
def sentiment_analysis():
    quarter_to_articles = request.json.get('quarter_to_articles')
    # Extract text from each quarter
    for articles_json in quarter_to_articles:
        for article_json in articles_json:
            # print("HELLO", file=sys.stderr)
            # print(f"URL: {article_json['url']}", file=sys.stderr)
            # feed = feedparser.parse(article_json['url'])
            # print(f"Feed: {feed}", file=sys.stderr)
            # for entry in feed.entries:
            #     url = entry.link
            article = Article(article_json['url'])
            article.download()
            article.parse()
            print(article.text, file=sys.stderr)
    return quarter_to_articles

# openai.api_key = os.getenv("OPENAI_API_KEY")

# @app.route('/filter_articles', methods=['POST'])
# def filter_articles():
#     # Extract the articles from the incoming JSON
#     company_name = request.json.get('company_name')
#     articles = request.json.get('articles', [])
#     filtered_articles = []
#     bad_articles = []

#     for article in articles:
#         # Concatenate the relevant information from the article
#         text_to_evaluate = f"Title: {article['title']}\nDescription: {article['description']}\nPublisher: {article['publisher']}"
        
#         # Here, you could call the GPT API to evaluate if the article is relevant or not
#         response = openai.Completion.create(
#           engine="text-davinci-003",
#           prompt=f"Given the following article title, description, and publisher information, is the following article relevant for {company_name}'s sentiment analysis? Provide 'Yes' or 'No', and nothing else.\n{text_to_evaluate}",
#           max_tokens=50
#         )
        
#         # Parse the response to decide if you should filter this article
#         answer = response.choices[0].text.strip()
#         if 'yes' in answer.lower():
#             filtered_articles.append(article)
#         else:
#             bad_articles.append(article)

#     # Return the filtered list of articles
#     print('FILTERED ARTICLES:')
#     print(filtered_articles, file=sys.stderr)
#     print('\nBAD ARTICLES:')
#     print(bad_articles, file=sys.stderr)
#     return jsonify(filtered_articles)

if __name__ == '__main__':
    app.run(port=8000, debug=True)