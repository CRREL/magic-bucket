"""Lambda function for the magic bucket.

This script takes one or more s3 record events and fans them out to:

    - An SQS message containing information about the source and target files.
    - An ECS task that will fetch the SQS message and process the files.
"""

import json
import logging
import os
import boto3

KEY_EXTENSION_BLACKLIST = [".json", ".md"]
OUTPUT_DIRNAME = "output"

sqs = boto3.client("sqs")
ecs = boto3.client("ecs")
logger = logging.getLogger()
logger.setLevel(logging.INFO)

SQS_QUEUE_URL = "https://sqs.us-east-1.amazonaws.com/605350515131/magic-bucket"
ECS_TASK = "magic-bucket"


def main(event, _):
    """Entrypoint."""
    message_sent = False
    for record in event["Records"]:
        key = record["s3"]["object"]["key"]
        if os.path.basename(os.path.dirname(key)) == OUTPUT_DIRNAME:
            logger.info(
                "Key parent directory is {}, not sending sqs message".format(
                    OUTPUT_DIRNAME))
            continue
        _, extension = os.path.splitext(key)
        if extension in KEY_EXTENSION_BLACKLIST:
            logger.info(
                "Key extension {} is blacklisted, not sending sqs message".format(extension))
            continue
        if send_sqs_message(record):
            message_sent = True
    if message_sent:
        run_ecs_task()
    return True


def send_sqs_message(record):
    """Sends an SQS message containing the record information."""
    message_body = json.dumps(record)
    logger.info("Sending SQS message to {}: {}".format(
        SQS_QUEUE_URL, message_body))
    response = sqs.send_message(
        QueueUrl=SQS_QUEUE_URL, MessageBody=message_body)
    logger.info("SQS message sent OK: {}".format(response))
    return True


def run_ecs_task():
    """Runs the hardcoded ECS task."""
    logger.info("Running ECS task: {}".format(ECS_TASK))
    response = ecs.run_task(taskDefinition=ECS_TASK, count=1)
    logger.info("ECS task run OK: {}".format(response))
    return True
