# Algorithmic Trading Pipeline

This is a project to make trades on political betting markets immediately after relevant news articles come out.

The [blog post](https://medium.com/neural-knot/algorithmic-trading-of-low-volume-markets-fda00bdf4b77#.7fuoa06hq) for this project explains more.

# How it Works

The project is a pipeline with three stages.  Each stage is connected to the others via Python queues.

The first stage is **Data Input**.  This is how news articles are fed to the project.  Currently, NewsAPI is used - however, this can easily be expanded to include additional sources.  In the future, this stage of the pipeline could be expanded to use other sources like Twitter, and assign reliability scores to certain inputs.

The second stage is **Data Analysis**.  This is where news articles are analyzed for:

1. Relevancy to markets that the project is set to monitor.

2. Implications to relevant markets (i.e. "will this article increase the YES or NO shares of market XXX?")

Data Analysis first uses the Google Cloud Language API to determine whether a given article is relevant.  It does so by extracting entities from the article's headline, then comparing them to relevant entities hardcoded in the config file.

If an article is determined to be relevant, it is then subjected to keyword analysis with the Wordnet corpus.  Target and anti-target keywords are hardcoded into the config; target keywords are meant to imply a "YES" outcome, and anti-target outcomes are meant to imply a "NO" outcome.  Features generated from keyword analysis are passed into an SVM, which generates probabilities that an article falls into the following categories:

1. Irrelevant / inconclusive

2. Implies a "NO" outcome

3. Implies a "YES" outcome

The third stage is the **Trader**.  The Trader takes the output from the Data Analysis stage, determines whether a trade is prudent, and makes a trade if so.  Any positions created by the Trader are automatically entered into a database and closed an hour later.

# Infrastructure

The project is automatically deployed to AWS via CodeDeploy.  During the deployment process, all files except for the following are deleted.  **All other files are deleted.**

1. The `logs` directory
2. The `db` directory

The `logs` directory contains log-files for each run; each run is assigned a unique identifier.  All relevant actions - for example, the Trader making a trade - are logged here.  The `db` directory contains information necessary to avoid duplicate trades, and to ensure that positions are closed.  **If you intend to run this program in production, it is recommended to update the project to use "real" database and logging infrastructure instead.**  On-disk options were used for rapid prototyping.

A monitoring script is run every hour on the instance.  This script will trigger an SNS notification with a message that includes the most recent occurrence of every log type (e.g. `Data Analysis` logs).  What you do with this notification depends on your configuration - a simple approach is to just subscribe to the SNS topic with your email, and monitor your email to make sure the program is working well.

# Required Environment Files

1. You must have a `config.json` file in the root of the project.

2. You must have a `google_auth.json` file in the root of the project.

Everything else will be handled, as long as you follow the deployment process below.

# Process for Deploying

1. Create a CodeDeploy project.  A guide for this can be found on the AWS site.

2. Create a SNS topic, a newsapi.org key, and Google Cloud credentials with access to the Cloud Language API.

3. Create your `config.json` and `google_auth.json` files - with the information from step 2 - and add them to an S3 bucket.  Sample files can be found in the project source.  These will automatically be pulled during the deployment process.

4. Create a CodeDeploy instance (if not already created).  This is basically an instance with the user data below.  Make sure the instance has Ubuntu installed (the scripts that handle deployment assume this).  Also, make sure it has access to the AWS CodeDeploy bucket for your region, and the config bucket you created during the last step.

```
#!/bin/bash
apt-get -y update
apt-get -y install awscli
apt-get -y install ruby
cd /home/ubuntu
aws s3 cp s3://YOUR_CONFIG_BUCKET/google_auth.json . --region YOUR_REGION
aws s3 cp s3://YOUR_CONFIG_BUCKET/config.json . --region YOUR_REGION
aws s3 cp s3://YOUR_CODEDEPLOY_BUCKET/latest/install . --region YOUR_REGION
chmod +x ./install
./install auto
sudo service codedeploy-agent start
```

5. Create a deploy via AWS CodeDeploy.

6. Monitor your SNS topic to ensure the program was started and is functioning as expected.  You can also SSH into the machine and check the logs if you're impatient.

# License

Copyright 2017 Daniel Ruskin & Jack Davis

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
