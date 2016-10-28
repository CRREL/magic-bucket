"""General utilities used for all magic bucket tasks."""

import json
import logging

import boto3
import botocore

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
