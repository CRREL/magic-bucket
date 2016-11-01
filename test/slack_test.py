import os

from magic_bucket import Slack

slack = Slack(os.environ["SLACK_TOKEN"], "pdal-translate", ":pdal:")
print slack.info("Information message")
print slack.success("Success message")
print slack.fail("Failure message")
