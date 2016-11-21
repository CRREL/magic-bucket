from task import Task


class PdalInfo(Task):
    """Runs `pdal info` on a file."""

    NAME = "pdal-info"

    def name(self):
        return self.NAME

    def process(self, filename):
        args = ["pdal", "info", "--all", filename]
        self.logger.info("Running {}".format(args))
        stdout = self.subprocess(args)
        output = filename + ".json"
        with open(output, "w") as f:
            f.write(stdout)
        return output

if __name__ == "__main__":
    import sys
    import boto3
    s3 = boto3.resource("s3")
    task = PdalInfo(None, s3.Object("", ""))
    print "Output:", task.process(sys.argv[1])
