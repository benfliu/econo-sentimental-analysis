from flask import Flask, request, jsonify
from flask_cors import CORS
from gnews import GNews
from dotenv import load_dotenv
import openai
import os
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta
import newspaper
from newspaper import Article
import feedparser
import tweepy
from forecasting import get_company_data, get_data, get_macroeconomic_data, forecast, evaluate
from transformers import pipeline
import pandas as pd

load_dotenv()
app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return "Hello, World!"

@app.route('/get_articles_by_quarter', methods=['GET'])
def get_articles_by_quarter():
    company_name = request.args.get('company_name', default='', type=str)
    today = datetime.now()
    interval_start = today - relativedelta(years=10, days=1)
    interval_end = interval_start + relativedelta(months=3)
    quarter_to_articles = []

    while interval_end < today:
        google_news = GNews(language='en', country='US', start_date=interval_start, end_date=interval_end, max_results=5)
        interval_articles = google_news.get_news(f'"{company_name}" news')
        quarter_to_articles.append(interval_articles)
        interval_start += relativedelta(months=3)
        interval_end += relativedelta(months=3)
    
    print(len(quarter_to_articles), file=sys.stderr)
    return jsonify(quarter_to_articles)

# @app.route('/get_tweets', methods=['GET'])
# def get_tweets():
#     company_name = request.args.get('company_name', default='', type=str)
#     auth = tweepy.AppAuthHandler(consumer_key="UXRusag6lI2AO0ZBLpXUB2uVW", consumer_secret= "xiQiYSnwUOLiOP8jhminCecBEoq2bXPM9349b1R6KouGGZ91r8")
#     api = tweepy.API(auth)
#     tweets = api.search_tweets(q = company_name)
#     return jsonify(tweets)

@app.route('/sentiment_analysis', methods=['POST'])
def sentiment_analysis():
    quarter_to_articles = request.json.get('quarter_to_articles')
    pipe = pipeline("text-classification", model="ProsusAI/finbert", return_all_scores = True)

    sentiments = pd.DataFrame(columns = ["Date", "Positive", "Negative", "Neutral"])

    # Extract text from each quarter
    for articles_json in quarter_to_articles:
        for article_json in articles_json:
            article = Article(article_json['url'])
            article.config.request_timeout = 10
            try:
                article.download()
                article.parse()
                output = pipe(article.text[:512])
                sentiments.loc[len(sentiments)] = [article_json["published date"]] + output_to_sentiment(output)
            except newspaper.article.ArticleException:
                continue
        
    return jsonify(sentiments.to_dict())

def output_to_sentiment (output):
    return [score['score'] for score in output[0] if score['label'] == 'positive'] + [score['score'] for score in output[0] if score['label'] == 'negative'] + [score['score'] for score in output[0] if score['label'] == 'neutral']

@app.route('/prediction', methods=['POST'])
def prediction():
    company_name = request.args.get('company_name', default='', type=str)
    sentiments = pd.DataFrame.from_dict(request.json.get('sentiments'), orient='columns')
    
    return jsonify(forecast(company_name, 2, sentiments = sentiments).to_dict(orient='records'))

@app.route('/evaluation', methods=['POST'])
def evaluation():
    company_name = request.args.get('company_name', default='', type=str)
    sentiments = pd.DataFrame.from_dict(request.json.get('sentiments'), orient='columns')
    
    return jsonify(evaluate(company_name, 5, sentiments = sentiments).to_dict(orient='records'))

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    company_name = request.args.get('company_name', default='', type=str)
    
    
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