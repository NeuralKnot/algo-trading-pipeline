import time

from google.cloud import language
from nltk.corpus import wordnet
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.externals import joblib
from sklearn.multiclass import OneVsRestClassifier
from sklearn import svm
from sklearn import preprocessing
from difflib import SequenceMatcher
class DataAnalysis:

    def __init__(self, config, logger, article_queue, score_queue, load_model=True):
        self.config = config
        self.logger = logger
        self.article_queue = article_queue
        self.score_queue = score_queue

        if load_model:
            self.load_model()

    # For use during training
    def create_model(self, training_articles):
        model = OneVsRestClassifier(svm.SVC(probability=True))

        features = []
        labels = []
        i = 0
        for article in training_articles:
            print("Generating features for article " + str(i) + "...")
            google_cloud_response = self.analyze_text_google_cloud(article["article"])
            relevant_entities = self.get_relevant_entities(google_cloud_response["entities"], article["market"]["entities"], article["market"]["wikipedia_urls"])

            # Only count this article if a relevant entity is present
            if relevant_entities:
                article_features = self.article_features(relevant_entities, article["market"], google_cloud_response, article["article"])
                features.append(article_features)
                labels.append(article["label"])
            else:
                print("Skipping article " + str(i) + "...")

            i = i + 1

        print("Performing feature scaling...")
        scaler = preprocessing.StandardScaler().fit(features)
        features_scaled = scaler.transform(features)

        print("Fitting model...")
        model.fit(features_scaled, labels)

        print("Saving model...")
        joblib.dump(scaler, "data_analysis/caler.pkl")
        joblib.dump(model, "data_analysis/model.pkl")

        print("Done!")

    # For use in prod
    def load_model(self):
        self.scaler = joblib.load("data_analysis/scaler.pkl")
        self.model = joblib.load("data_analysis/model.pkl")

    # Processes the given article and stores the results in the queue
    def handle_article(self, article):
        self.logger.log("Data Analysis", "informative", "Received article: " + article["title"])

        # Run the article through Google Cloud Language API,
        # and figure out if it relates to a relevant entity.
        google_cloud_response = self.analyze_text_google_cloud(article)
        relevant_entities_and_markets = self.get_relevant_markets(google_cloud_response["entities"])

        # For each market, come up with a score to represent
        # whether the article represents a strong positive
        # or negative statement.
        # Queue this for the trader.
        for entities_and_market in relevant_entities_and_markets:
            score = self.score_article(entities_and_market[0], entities_and_market[1], google_cloud_response, article)
            self.logger.log("Data Analysis", "informative", "Scored article for market " + entities_and_market[1]["contract_id"] + ": " + article["title"])

            result = {
                "market": entities_and_market[1],
                "article": article,
                "score": score
            }
            self.queue_result(result)

    def analyze_text_google_cloud(self, article):
        client = language.Client()
        document = client.document_from_text(article["title"])
        annotations = document.annotate_text()

        return {
            "entities": annotations.entities,
            "tokens": annotations.tokens,
            "sentiment": annotations.sentiment
        }

    def score_article(self, relevant_entities, market, google_cloud_response, article):
        features = self.article_features(relevant_entities, market, google_cloud_response, article)
        features_scaled = self.scaler.transform([features])[0]

        score = self.model.predict_proba([features_scaled])[0]

        return score

    def array_avg(arr):
        total = 0.0
        for item in arr:
            total += item

        return total / len(arr)

    def article_features(self, relevant_entities, market, google_cloud_response, article):
        features = []

        # Vectorize headline and get unique words
        article_headline = article["title"]
        vec = CountVectorizer()
        headline_features = vec.fit_transform([article_headline]).toarray()
        headline_words = vec.get_feature_names()

        # Perform similarity check against target and anti-target words
        target_words_matched = []
        target_similarities = []
        anti_target_words_matched = []
        anti_target_similarities = []
        for headline_word in headline_words:
            try:
                headline_word_synset = wordnet.synsets(headline_word)[0]
            except IndexError:
                # No synset available for this word, skip
                continue

            for target_word in market["target_words"]:
                try:
                    target_word_synset = wordnet.synsets(target_word)[0]
                except IndexError:
                    # No synset available for this word, skip
                    continue

                similarity = headline_word_synset.path_similarity(target_word_synset) or 0
                target_similarities.append(similarity)

                if similarity > 0.5 and target_word not in target_words_matched:
                    target_words_matched.append(target_word)

            for anti_target_word in market["anti_target_words"]:
                try:
                    anti_target_word_synset = wordnet.synsets(anti_target_word)[0]
                except IndexError:
                    # No synset available for this word, skip
                    continue

                similarity = headline_word_synset.path_similarity(anti_target_word_synset) or 0
                anti_target_similarities.append(similarity)

                if similarity > 0.5 and target_word not in anti_target_words_matched:
                    anti_target_words_matched.append(target_word)

        # Compute avg/max similarities
        features.append(max(target_similarities or [0]))
        features.append(max(anti_target_similarities or [0]))
        features.append(len(target_words_matched))
        features.append(len(anti_target_words_matched))

        return features

    def get_relevant_entities(self, google_cloud_entities, target_entities, target_wikipedia_urls):
        entities_to_return = []
        target_wikipedia_urls_lower = [target_wikipedia_url.lower() for target_wikipedia_url in target_wikipedia_urls]

        for google_cloud_entity in google_cloud_entities:
            # Look at Wikipedia URLs
            if google_cloud_entity.wikipedia_url and google_cloud_entity.wikipedia_url.lower() in target_wikipedia_urls_lower:
                entities_to_return.append(google_cloud_entity.name)
                continue

            # Look at names
            a = google_cloud_entity.name.lower().split(" ")
            for target_entity in target_entities:
                b = target_entity.lower().split(" ")

                if google_cloud_entity in entities_to_return:
                    break

                for google_cloud_entity_part in a:
                    for target_entity_part in b:
                        ratio = SequenceMatcher(None, google_cloud_entity_part, target_entity_part).ratio()

                        if ratio > 0.7:
                            entities_to_return.append(google_cloud_entity.name)
                            break

                    if google_cloud_entity in entities_to_return:
                        break

        return entities_to_return

    def get_relevant_markets(self, google_cloud_entities):
        markets_and_entities = []
        for market in self.config["markets"]:
            relevant_entities = self.get_relevant_entities(google_cloud_entities, market["entities"], market["wikipedia_urls"])

            if relevant_entities:
                markets_and_entities.append([relevant_entities, market])

        return markets_and_entities

    # Stores the result in the result queue
    def queue_result(self, result):
        self.score_queue.put(result)

    # Entry point for process
    def run(self):
        try:
            while True:
                article = self.article_queue.get(True) # Gets articles from the queue and analyzes them
                self.handle_article(article)
        except Exception as e:
            self.logger.log("Data Analysis", "error", "Crashed: " + str(e))
