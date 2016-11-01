import json
import os

from ..exceptions import MagicBucketException
from task import Task


class MissingConfigFile(MagicBucketException):
    """No configuration file was found."""

    def __init__(self):
        super(MissingConfigFile, self).__init__(
            "Missing configuration file for pdal translate")


class InvalidConfig(MagicBucketException):
    pass


class PdalTranslate(Task):
    """Runs `pdal translate` on a file."""

    DEFAULT_CONFIG_FILE = "config.json"
    DEFAULT_FILTERS_FILE = "filters.json"
    DEFAULT_OUTPUT_DIR = "output"
    NAME = "pdal-translate"

    def __init__(self, magic_bucket, s3_object):
        super(PdalTranslate, self).__init__(magic_bucket, s3_object)
        self.config_file = self.DEFAULT_CONFIG_FILE
        self.filters_file = self.DEFAULT_FILTERS_FILE
        self.output_dir = self.DEFAULT_OUTPUT_DIR

    def name(self):
        return self.NAME

    def process(self, filename):
        if not os.path.isfile(self.config_file):
            if not self.download_config_file():
                raise MissingConfigFile()
        with open(self.config_file) as f:
            try:
                config = json.load(f)
            except ValueError as e:
                raise InvalidConfig("Invalid JSON configuration: {}".format(e))

        filters = config.get("filters")
        output_ext = config.get("output_ext")
        additional_args = config.get("args")

        if output_ext:
            output = os.path.splitext(filename)[0] + output_ext
        else:
            output = filename
        os.mkdir(self.output_dir)
        output = os.path.join(self.output_dir, output)

        args = ["pdal", "translate", "-i", filename, "-o", output]
        if filters:
            with open(self.filters_file, "w") as f:
                json.dump(filters, f)
            args.extend(["--json", self.filters_file])
        if additional_args:
            args.extend(additional_args)

        self.logger.info("Running {}".format(args))
        stdout = self.subprocess(args)
        self.logger.info("Complete: {}".format(stdout))
        return output

    def download_config_file(self):
        """Downloads a configuration file from the object's directory."""
        return (self._download_sidecar_config_file() or
                self._download_directory_config_file())

    def _download_sidecar_config_file(self):
        key = self.key + ".json"
        return self.magic_bucket.download_file(self.bucket_name, key,
                                               self.config_file)

    def _download_directory_config_file(self):
        key = os.path.join(os.path.dirname(self.key), self.config_file)
        return self.magic_bucket.download_file(self.bucket_name, key,
                                               self.config_file)
