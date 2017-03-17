import os
import glob
import arrow
import boto3
import json
from sh import tail

# Open most recently edited log file, and get last 500 lines
newest_file = open(max(glob.iglob("logs/*.txt"), key=os.path.getctime))
newest_file_lines = tail("-5000", newest_file.name, _iter=True)

# Go through file and get last time for each log source
log_sources = {}
for line in newest_file_lines:
    split = line.split("[")

    # Extract relevant info from logline, and remove brackets
    log_time = split[1].replace("]", "").replace(" ", "")
    log_source = split[2].replace("]", "").replace(" ", "")

    # Parse time
    log_time_parsed = arrow.get(log_time)

    log_sources[log_source] = log_time_parsed

# Compile message with data
messages = []
messages.append("Algo Trading Status Check (Source: Last Time (Minutes Relative to Now))")
for log_source in log_sources.keys():
    relative_hours = (arrow.now() - log_sources[log_source]).seconds / 60
    messages.append(log_source + ": " + str(log_sources[log_source]) + "(" + str(round(relative_hours, 3)) + " minutes ago)")

# Load topic ARN for SNS notification
topic_arn = json.load(open("config.json"))["monitoring"]["sns_topic"]

# Trigger SNS notification
sns = boto3.resource("sns", region_name="us-west-2")
topic = sns.Topic(topic_arn)
topic.publish(
    Message="\n".join(messages),
    Subject="Algo Trading Monitoring Message"
)
