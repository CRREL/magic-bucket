import os

from task import Task


class Rimtatls(Task):
    """Riegl's rimtatls correction executable."""

    NAME = "rimtatls"

    def name(self):
        return self.NAME

    def process(self, filename):
        output = os.path.splitext(filename)[0] + ".mta.rxp"
        args = ["rimtatls", filename, output]
        self.logger.info("Running {}".format(args))
        stdout = self.subprocess(args)
        self.logger.info("Complete: {}".format(stdout))
        return output
