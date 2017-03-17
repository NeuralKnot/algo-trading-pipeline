from data_input import news_api

import time
import datetime
import arrow
from tinydb import *

class DataInput:

    def __init__(self, article_queue, logger, config):
        self.article_queue = article_queue
        self.logger = logger
        self.config = config

        self.sources = []
        for source in config["data_input"]["sources"]:
            self.sources.append({
                "news_api_name": source,
                "news_api_instance": news_api.NewsApi(
                    config["data_input"]["news_api"]["api_key"],
                    source,
                    logger
                ),
                "articles_db": TinyDB("db/" + source + ".newsapi.db.json")
            })

    # Continuously polls for new articles and adds them to the article queue
    def poll_for_articles(self):
        while True:
            at = 0
            for source in self.sources:
                self.logger.log("Data Input", "informative", "Polling: " + source["news_api_name"])

                articles = source["news_api_instance"].get_articles()
                if articles is not None:
                    for article in articles:
                        # Skip duplicates
                        q = Query()
                        if len(self.sources[at]["articles_db"].search(q.title == article["title"])) == 0:
                            self.queue_article(article)
                            self.sources[at]["articles_db"].insert({"title": article["title"], "at": str(arrow.now())})

                at = at + 1

            # Sleep for interval time
            time.sleep(self.config["data_input"]["poll_interval"])

    # Adds the given article to the queue
    def queue_article(self, article):
        self.logger.log("Data Input", "informative", "Article: " + article["title"])
        self.article_queue.put(article)

    # Prune all sources' databases
    def prune_databases(self):
        for source in self.sources:
            self.logger.log("Data Input/Pruner", "informative", "Pruning: " + source["news_api_name"])

            db = source["articles_db"]

            q = Query()
            test_func = lambda at: arrow.get(at) < (arrow.now() - datetime.timedelta(days=1))
            docs = db.search(q.at.test(test_func))

            eids = [doc.eid for doc in docs]
            db.remove(eids=eids)

    # Entry point for process
    def run(self):
        try:
            self.poll_for_articles()
        except Exception as e:
            self.logger.log("Data Input", "error", "Crashed: " + str(e))
