import os

from ..exceptions import MagicBucketException
from task import Task


class MissingFixedFile(MagicBucketException):
    pass


class ApeNearFieldPrcs(Task):
    """Run ATLAS's near-field-prcs cpd."""

    DEFAULT_FIXED_LAZ = "150728_180208.mta.laz"
    DEFAULT_FIXED = "150728_180208.mta.las"
    FIXED_S3_KEY = "pdal-translate/ATLAS/near-field-prcs/output/150728_180208.mta.laz"
    NAME = "ape-near-field-prcs"

    def __init__(self, magic_bucket, s3_object):
        super(ApeNearFieldPrcs, self).__init__(magic_bucket, s3_object)
        self.fixed_laz = self.DEFAULT_FIXED_LAZ
        self.fixed = self.DEFAULT_FIXED

    def name(self):
        return self.NAME

    def process(self, laz_filename):
        if not os.path.isfile(self.fixed):
            if not self.download_fixed_laz():
                raise MissingFixedFile()
            self.subprocess(["pdal", "translate", self.fixed_laz, self.fixed])
        filename = os.path.splitext(laz_filename)[0] + ".las"
        self.subprocess(["pdal", "translate", laz_filename, filename])
        output = os.path.splitext(filename)[0] + ".dat"
        args = ["/root/.cargo/bin/ape", "cpd", self.fixed, filename, output]
        self.logger.info("Running {}".format(args))
        stdout = self.subprocess(args)
        self.logger.info("Complete: {}".format(stdout))
        return output

    def download_fixed_laz(self):
        return self.magic_bucket.download_file(self.bucket_name,
                                               self.FIXED_S3_KEY,
                                               self.fixed_laz)
