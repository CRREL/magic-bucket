#!/usr/bin/env python

"""Run `pdal translate` from a magic bucket."""

import json
import logging
import os
import subprocess

from magic_bucket import MagicBucket, Slack

CONFIG_JSON = "config.json"
FILTERS_JSON = "filters.json"
OUTPUT_DIRNAME = "output"

logging.basicConfig()
logger = logging.getLogger("magic-bucket")
logger.setLevel(logging.INFO)

magic_bucket = MagicBucket(os.environ["AWS_REGION"], os.environ["SQS_QUEUE_URL"])
slack = Slack(os.environ["SLACK_TOKEN"], "pdal-translate", ":pdal:")

class PdalTranslateError(Exception):
    def __init__(self, message):
        super(PdalTranslateError, self).__init__(message)

def main():
    for s3_object in magic_bucket.s3_objects():
        slack.info("Received `{}`".format(s3_object.key))
        try:
            output = pdal_translate(s3_object)
        except PdalTranslateError as e:
            slack.fail(str(e))
        except Exception as e:
            slack.fail(str(e))
            raise e
        else:
            slack.success("Successfully translated `{}` into `{}`, url: s3://{}/{}".format(s3_object.key, output, s3_object.bucket_name, output))

def pdal_translate(s3_object):
    bucket_name = s3_object.bucket_name
    basename = os.path.basename(s3_object.key)
    logger.info("Downloading {} as {}".format(s3_object.key, basename))
    s3_object.download_file(basename)
    root, extension = os.path.splitext(basename)

    if extension == ".zip":
        subprocess.check_call(["unzip", basename])
        basename = root
    elif extension == ".gz":
        subprocess.check_call(["gunzip", basename])
        basename = root

    if not os.path.isfile(CONFIG_JSON):
        config_json_key = s3_object.key + ".json"
        logger.info("{} not found on filesystem, checking for {} in bucket {}".format(CONFIG_JSON, config_json_key, bucket_name))
        if not magic_bucket.download_file(bucket_name, config_json_key, CONFIG_JSON):
            bucket_config_json_key = os.path.join(os.path.dirname(s3_object.key), CONFIG_JSON)
            logger.info("{} not on s3, checking for {} in bucket {}".format(config_json_key, bucket_config_json_key, bucket_name))
            if not magic_bucket.download_file(bucket_name, bucket_config_json_key, CONFIG_JSON):
                logger.error("No config.json found in search locations, aborting")
                raise PdalTranslateError("No config.json found in search locations")

    with open(CONFIG_JSON) as config_json_file:
        try:
            config_json = json.load(config_json_file)
        except ValueError as e:
            raise PdalTranslateError("Invalid configuration file: {}".format(e))

    filters_json = config_json.get("filters")
    output_ext = config_json.get("output_ext")
    additional_args = config_json.get("args")

    output, extension = os.path.splitext(basename)
    if output_ext:
        extension = output_ext
    output += ".output" + extension

    args = ["pdal", "translate", "-i", basename, "-o", output]
    if filters_json is not None:
        with open(FILTERS_JSON, "w") as filters_json_file:
            json.dump(filters_json, filters_json_file)
        args.extend(["--json", FILTERS_JSON])
    if additional_args is not None:
        args.extend(additional_args)
    logger.info("Running {}".format(args))
    process = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdout, _) = process.communicate()
    if process.returncode != 0:
        logger.error("Error when running pdal translate")
        raise PdalTranslateError("Error while running {} (returncode {}): {}".format(args, process.returncode, stdout))
    os.remove(basename)
    os.remove(CONFIG_JSON)
    if filters_json:
        os.remove(FILTERS_JSON)

    output_key = os.path.join(os.path.dirname(s3_object.key), OUTPUT_DIRNAME, os.path.splitext(basename)[0] + extension)
    logger.info("Uploading {} to {}".format(output, output_key))
    magic_bucket.upload_file(output, bucket_name, output_key)
    os.remove(output)
    return output_key

main()
