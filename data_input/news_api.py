import json
import urllib3.request
import certifi


# Interfaces with the newsapi.org API
class NewsApi:

    def __init__(self, api_key, source, logger):
        self.apiKey = api_key
        self.source = source
        self.logger = logger
        self.sort_error_displayed = False
        self.http = urllib3.PoolManager(
            cert_reqs = "CERT_REQUIRED", # Force certificate check.
            ca_certs = certifi.where(),  # Path to the Certifi bundle.
        )

    # Retrieves articles from source
    def get_articles(self, sort='latest'):
        request_uri = "https://newsapi.org/v1/articles"
        request_uri += "?apiKey=" + self.apiKey
        request_uri += "&source=" + self.source
        request_uri += "&sortBy=" + sort

        response = self.http.request("GET", request_uri)
        jsonobj = json.loads(response.data.decode("utf-8"))
        if not jsonobj["status"] == "error":
            return jsonobj["articles"]
        else:
            if not self.sort_error_displayed:
                self.sort_error_displayed = True
                self.logger.log("News API", "error", "Error: the source \'" + self.source + "\' cannot be sorted by \'latest.\'" + " Changing the sort to \'top\'")
            return self.get_articles(sort='top')
