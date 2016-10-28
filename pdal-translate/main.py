"""Run `pdal translate` from a magic bucket."""

import logging
import os

from magic_bucket import MagicBucket

logging.basicConfig()
logger = logging.getLogger("magic-bucket")
logger.setLevel(logging.INFO)

magic_bucket = MagicBucket(os.environ["AWS_REGION"], os.environ["SQS_QUEUE_URL"])

def main():
    for s3_object in magic_bucket.s3_objects():
        print s3_object.bucket_name, s3_object.key

main()
