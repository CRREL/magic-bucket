from slackclient import SlackClient


class Slack(object):
    """Wrapper around the slack client to provide utility methods."""

    DEFAULT_CHANNEL = "#magic-bucket-notify"
    DEFAULT_USERNAME = "bucketbot"

    def __init__(self, token):
        """Creates a new slack interface."""
        self.client = SlackClient(token)
        self.channel = self.DEFAULT_CHANNEL
        self.username = self.DEFAULT_USERNAME

    def info(self, message):
        """Send an information message."""
        self.post_message(message, message_emoji=":information_desk_person:")

    def success(self, message):
        """Send an success message."""
        self.post_message(message, message_emoji=":the_horns:")

    def fail(self, message):
        """Send a fail message."""
        self.post_message(message, message_emoji=":sadpanda:")

    def post_message(self, message, message_emoji=None):
        """Post a message to the pre-configured channel."""
        if message_emoji is not None:
            message = "{} {}".format(message_emoji, message)
        self.client.api_call(
            "chat.postMessage", channel=self.channel,
            text=message, username=self.username)
