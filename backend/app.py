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
        google_news = GNews(language='en', country='US', start_date=interval_start, end_date=interval_end, max_results=1)
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
    print('BEFORE REQUEST TO JSON',file=sys.stderr);
    quarter_to_articles = request.json.get('quarter_to_articles')
    print('AFTER REQUEST TO JSON',file=sys.stderr);
    pipe = pipeline("text-classification", model="ProsusAI/finbert", return_all_scores = True)
    print('AFTER PIPELINE',file=sys.stderr);

    sentiments = pd.DataFrame(columns = ["Date", "Positive", "Negative", "Neutral"])

    # Extract text from each quarter
    for articles_json in quarter_to_articles:
        for article_json in articles_json:
            article = Article(article_json['url'])
            article.config.request_timeout = 10
            try:
                article.download()
                article.parse()
                print(article.text, files=sys.stderr)
                output = pipe(article.text[:512])
                sentiments.loc[len(sentiments)] = [article_json["published date"]] + output_to_sentiment(output)
            except newspaper.article.ArticleException:
                continue
        
    return jsonify(sentiments.to_dict())

def output_to_sentiment (output):
    return [score['score'] for score in output[0] if score['label'] == 'positive'] + [score['score'] for score in output[0] if score['label'] == 'negative'] + [score['score'] for score in output[0] if score['label'] == 'neutral']

@app.route('/prediction', methods=['POST'])
def prediction():
    company_name = request.json.get('company_name')
    sentiments = pd.DataFrame.from_dict(request.json.get('sentiments'), orient='columns')
    data, predictions = forecast(company_name, 2, sentiments = sentiments)
    
    return jsonify({"data": data.to_dict(), "predictions": predictions.to_dict()})

@app.route('/get_data', methods=['POST'])
def get_data():
    metric = request.json.get('metric')
    all_data = request.json.get('all_data')
    print('TEST!!!!', files=sys.ifidf)
    metric_data = all_data.get('data').get(metric)
    quarters = []
    values = []
    for quarter in metric_data:
        quarters.append(quarter)
        values.append(metric_data.get(quarter))
    clean_data = {
        "x_vals": quarters,
        "y_label": f"{metric} (Actual)",
        "vals": values
    }
    return jsonify(clean_data)

@app.route('/get_predictions', methods=['POST'])
def get_predictions():
    metric = request.json.get('metric')
    all_data = request.json.get('all_data')
    metric_predictions = all_data.get('predictions').get(metric)
    quarters = []
    values = []
    for quarter in metric_predictions:
        quarters.append(quarter)
        values.append(metric_predictions.get(quarter))
    clean_predictions = {
        "x_vals": quarters,
        "y_label": f"{metric} (Predicted)",
        "vals": values
    }
    return jsonify(clean_predictions)

@app.route('/evaluation', methods=['POST'])
def evaluation():
    company_name = request.json.get('company_name')
    sentiments = pd.DataFrame.from_dict(request.json.get('sentiments'), orient='columns')
    
    return jsonify(evaluate(company_name, 5, sentiments = sentiments).to_dict(orient='records'))
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    company_name = request.args.get('company_name', default='', type=str)
    # percent_change = request.args.get('percent_change', default=0.0, type=float)

    google_news = GNews(language='en', country='US', max_results = 1)
    articles = google_news.get_news(f'"{company_name}" news')
    titles = []
    for article in articles:
        titles.append(article['title'])
    
    macro_text = """The Conference Board forecasts that US economic growth will buckle under mounting headwinds early next year, leading to a very short and shallow recession. This outlook is associated with numerous factors, including, elevated inflation, high interest rates, dissipating pandemic savings, rising consumer debt, lower government spending, and the resumption of mandatory student loan repayments. We forecast that real GDP will grow by 2.2 percent in 2023, and then fall to 0.8 percent in 2024.

                        US consumer spending has held up remarkably well this year despite elevated inflation and higher interest rates. However, this trend cannot hold, in our view. Real disposable personal income growth is flat, pandemic savings are dwindling, and household debt is rising. Additionally, new student loan repayment requirements will begin to impact many consumers starting in October. Thus, we forecast that overall consumer spending growth will slow towards yearend and then contract in Q1 2024 and Q2 2024. As inflation and interest rates abate later in 2024, we expect consumption to begin to expand once more.

                        Meanwhile, following weak growth in Q1 2023, business investment bounced back in Q2 2023 despite interest rate increases. This was largely due to a surge in business spending on equipment (especially computing and transportation equipment) and elevated investment in structures (especially in manufacturing). However, we expect this trend to gradually reverse as US consumption begins to soften and interest rates continue to rise (we believe the Fed will raise rates by 25 basis points once more this year, likely in November). Residential investment, which has already contracted significantly, should start to bottom out later this year and then rise on lower interest rates and strong demand in 2024.

                        Government spending represented one of the few positive growth drivers for 2023 as federal non-defense spending benefited from outlays associated with infrastructure investment legislation passed in 2021 and 2022. However, reductions in discretionary outlays ($1.5 Trillion over 10 years) detailed in the Fiscal Responsibility Act, which averted the debt ceiling crisis, will limit overall government spending and act as a drag on growth later this year and early next.

                        On inflation, we expect to see progress over the coming quarters, but the path will probably be bumpy. Energy prices have been rising in recent weeks and will likely rise further on the back on conflict in the Middle East. However, progress in rental prices, which were previously a significant contributor to inflation, are beginning to cool inflation data. We expect year-over-year inflation readings to remain at about 3 percent at 2023 yearend and that the Fed’s 2 percent target will not be achieved until the end of 2024.

                        Labor market tightness has been remarkably persistent but we expect it to moderate somewhat over the coming quarters. However, relative to previous economic downturns we expect the labor market to hold up well due to persistent shortages in some industries and labor hoarding in others. This should prevent overall economic growth from slipping too deeply into contractionary territory and facilitate a rebound next year.

                        Looking into late 2024, we expect the volatility that dominated the US economy over the pandemic period to diminish. In the second half of 2024, we forecast that overall growth will return to more stable pre-pandemic rates, inflation will drift closer to 2 percent, and the Fed will lower rates to near 4 percent. However, due to an aging labor force we expect tightness in the labor market to remain an ongoing challenge for the foreseeable future."""

    industry_name = openai.Completion.create(
      model="gpt-3.5-turbo",
      prompt="What industry is " + company_name + " in? Respond with only the industry name."
    )

    industry_name = industry_name['choices'][0]['text'].strip()
    industry_articles = google_news.get_news(f'"Projections for {industry_name} sector" news')
    industry_text = industry_articles[0]['text']

    summary = openai.Completion.create(
        model="gpt-4",
        prompt = "First give me a one sentence summary of the company " + company_name
                + ". Next give me a one sentence summary of it's financial history. "
                + "Next, give a one sentence summary about what it has been in the news for, using this list of article titles: " + titles
                + ". Next give a one sentence summary of the state of the " + industry_name + " industry, based on the text below. "
                + "Next give a one sentence summary about U.S. economy projections, based on the text below."
                + "Next give me a one sentence conclusion. Do all of this in 5 sentences. Here are the articles to read:\n\n"
                + industry_text + "/n/n" + macro_text         
    )

@app.route('/generate_model_sum', methods=['POST'])
def generate_model_sum():
    company_name = request.args.get('company_name', default='', type=str)
    stock_change


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