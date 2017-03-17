from data_analysis import DataAnalysis
import json
import csv

# Load config
config = json.load(open("../config.json"))

# Load markets/articles
articles_csv = csv.reader(open("articles.csv"))

# Parse markets/articles
articles = []
for row in articles_csv:
    if row[0] == "Article Title":
        # Skip header
        continue

    article_obj = {}
    article_obj["article"] = {
        "title": row[0]
    }
    article_obj["market"] = {
        "symbol": "TEST_MARKET",
        "entities": row[1].split(","),
        "wikipedia_urls": row[2].split(","),
        "target_words": row[3].split(","),
        "anti_target_words": row[4].split(",")
    }
    article_obj["label"] = int(row[5])

    articles.append(article_obj)

da = DataAnalysis(config, load_model=False)
da.create_model(articles)
da.load_model()
