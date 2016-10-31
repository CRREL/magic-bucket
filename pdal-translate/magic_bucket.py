"""General utilities used for all magic bucket tasks."""

import json
import logging

import boto3
import botocore
from slackclient import SlackClient

class MagicBucket(object):
    """Utility class for operations that will be common between tasks."""

    def __init__(self, region, sqs_queue_url):
        self.logger = logging.getLogger("magic-bucket")
        self.s3 = boto3.resource("s3", region_name=region)
        sqs = boto3.resource("sqs", region_name=region)
        self.sqs_queue = sqs.Queue(sqs_queue_url)

    def receive_message(self):
        """Fetches a message from the sqs queue.

        Does *not* delete the message. Returns None if no message is received.
        """
        messages = self.sqs_queue.receive_messages(MaxNumberOfMessages=1)
        if messages:
            return messages[0]
        else:
            return None

    def consume_messages(self):
        """Fetches messages from the sqs queue, then removes them after they are returned from the generator."""
        while True:
            message = self.receive_message()
            if message is None:
                break
            else:
                message.delete()
                self.logger.info("Deleted message {} from sqs queue {}".format(message.receipt_handle, self.sqs_queue.url))
                yield message

    def s3_objects(self):
        """Generator over the s3 objects referenced by the sqs messages.

        This generator is destructive; it deletes the sqs messages before returning the s3 object.
        """
        for message in self.consume_messages():
            record = json.loads(message.body)
            bucket_name = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]
            yield self.s3.Object(bucket_name, key)

    def download_file(self, bucket_name, key, filename):
        """Downalods an s3 file to `filename`, as specified by a `bucket_name` and `key`.

        Returns True if the download is successful, False otherwise.
        """
        try:
            self.s3.Object(bucket_name, key).download_file(filename)
        except botocore.exceptions.ClientError as e:
            error_code = int(e.response["Error"]["Code"])
            if error_code == 404:
                return False
            else:
                raise e
        return True

    def upload_file(self, filename, bucket_name, key):
        """Uploads an s3 file."""
        self.s3.Object(bucket_name, key).upload_file(filename)


class Slack(object):
    """Wrapper around the slack client to provide utility methods."""

    DEFAULT_CHANNEL = "#magic-bucket"

    def __init__(self, token, username, icon_emoji):
        """Creates a new slack interface."""
        self.client = SlackClient(token)
        self.channel = self.DEFAULT_CHANNEL
        self.username = username
        self.icon_emoji = icon_emoji

    def info(self, message):
        """Send an information message."""
        self.post_message(message, message_emoji=":information_desk_person:")

    def success(self, message):
        """Send an success message."""
        self.post_message(message, message_emoji=":the_horns:")

    def fail(self, message):
        """Send a fail message."""
        self.post_message(message, message_emoji=":sadpanda:")

    def post_message(self, message, message_emoji=None):
        """Post a message to the pre-configured channel."""
        if message_emoji is not None:
            message = "{} {}".format(message_emoji, message)
        self.client.api_call("chat.postMessage", channel=self.channel, text=message, username=self.username, icon_emoji=self.icon_emoji)
