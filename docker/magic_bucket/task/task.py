import logging
import os
import shutil
import subprocess

from ..exceptions import MagicBucketException


class MissingS3File(MagicBucketException):
    """The s3 file is missing."""

    def __init__(self, s3_object):
        super(MissingS3File, self).__init__(
            "Missing s3 file: {}/{}".format(s3_object.bucket_name,
                                            s3_object.key))


class SubprocessError(MagicBucketException):
    """Some subprocess exited improperly."""

    def __init__(self, called_process_error):
        super(SubprocessError, self).__init__(
            "Subprocess error: {} with output {}".format(
                called_process_error, called_process_error.output))
        self.output = called_process_error.output
        self.returncode = called_process_error.returncode


class Task(object):
    """A generic magic bucket task."""

    DEFAULT_WORK_DIRECTORY = "work"
    DEFAULT_S3_OUTPUT_DIRECTORY = "output"

    def __init__(self, magic_bucket, s3_object):
        self.magic_bucket = magic_bucket
        self.s3_object = s3_object
        self.bucket_name = s3_object.bucket_name
        self.key = s3_object.key
        self.work_directory = self.DEFAULT_WORK_DIRECTORY
        self.s3_output_directory = self.DEFAULT_S3_OUTPUT_DIRECTORY
        self.logger = logging.getLogger("magic-bucket")

    def run(self):
        """Runs this task."""
        self.logger.info("Creating {}".format(self.work_directory))
        os.mkdir(self.work_directory)
        os.chdir(self.work_directory)
        try:
            filename = self.download_and_extract()
            output = self.process(filename)
            s3_object = self.upload(output)
        finally:
            os.chdir("..")
            self.logger.info("Removing {}".format(self.work_directory))
            shutil.rmtree(self.work_directory)
        return s3_object

    def download_and_extract(self):
        """Downloads and extracts the specified file."""
        basename = os.path.basename(self.key)
        self.logger.info("Downloading {} to {}".format(
            self.s3_object.key, basename))
        if not self.magic_bucket.download_object(self.s3_object, basename):
            raise MissingS3File(self.s3_object)
        root, extension = os.path.splitext(basename)
        if extension == ".zip":
            self.logger.info("Unzipping {}".format(basename))
            self.subprocess(["unzip", "-o", basename])
            basename = root
        elif extension == ".gz":
            self.logger.info("Gunzipping {}".format(basename))
            self.subprocess(["gunzip", "-f", basename])
            basename = root
        return basename

    def process(self, filename):
        raise NotImplementedError

    def name(self):
        raise NotImplementedError

    def upload(self, filename):
        """Uploads the filename back to the s3 bucket.

        The file will be named just the basename of the filename, to support
        output files in the subdirectories.
        """
        key = os.path.join(os.path.dirname(self.key),
                           self.s3_output_directory,
                           os.path.basename(filename))
        self.logger.info("Uploading {} to {}".format(filename, key))
        return self.magic_bucket.upload_file(filename, self.bucket_name, key)

    def subprocess(self, args):
        """Runs a subprocess."""
        try:
            return subprocess.check_output(args, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            raise SubprocessError(e)


if __name__ == "__main__":
    from magic_bucket import MagicBucket
    logging.basicConfig()
    logger = logging.getLogger("magic-bucket")
    logger.setLevel(logging.INFO)
    magic_bucket = MagicBucket(
        "us-east-1",
        "https://sqs.us-east-1.amazonaws.com/605350515131/magic-bucket")
    keys = ["pdal-translate/to-laz/simple.las",
            "pdal-translate/to-laz/simple.las.zip",
            "pdal-translate/to-laz/simple.las.gz"]

    class LaszipTask(Task):

        def process(self, filename):
            output = os.path.splitext(filename)[0] + ".laz"
            self.subprocess(["pdal", "translate", filename, output])
            return output

    for key in keys:
        s3_object = magic_bucket.s3_object("crrel-magic-bucket", key)
        task = LaszipTask(magic_bucket, s3_object)
        task.run()
