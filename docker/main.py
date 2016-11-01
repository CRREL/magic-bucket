#!/usr/bin/env python

"""Run the magic bucket."""

import logging
import os

from magic_bucket import (MagicBucket, create_task, UnknownTask, Slack,
                          MagicBucketException)


def main():
    """Handle each s3 object, as retrieved from the SQS queue."""
    logging.basicConfig()
    logger = logging.getLogger("magic-bucket")
    logger.setLevel(logging.INFO)
    magic_bucket = MagicBucket(os.environ["AWS_REGION"],
                               os.environ["SQS_QUEUE_URL"])
    slack = Slack(os.environ["SLACK_TOKEN"])
    try:
        for s3_object in magic_bucket.s3_objects():
            try:
                task = create_task(magic_bucket, s3_object)
            except UnknownTask as e:
                slack.fail("Unknown task: *{}*".format(e.task_name))
                continue
            slack.info(
                "Running *{}* on `{}`".format(task.name(), s3_object.key))
            try:
                output = task.run()
            except MagicBucketException as e:
                slack.fail("Error while running *{}* on *{}*: {}".format(
                    task.name(), s3_object.key, e))
            slack.success("Completed *{}* on `{}`, uploaded to s3://{}/{}"
                          .format(task.name(), s3_object.key,
                                  output.bucket_name, output.key))
    except Exception as e:
        slack.fail("Unhandled exception, aborting: {}".format(e))
        raise e


if __name__ == "__main__":
    main()
