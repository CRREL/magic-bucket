import os

from ..exceptions import MagicBucketException
from pdal_translate import PdalTranslate
from rimtatls import Rimtatls


class UnknownTask(MagicBucketException):
    """The provided task name is unknown."""
    def __init__(self, task_name):
        super(UnknownTask, self).__init__("Unknown task: {}".format(task_name))
        self.task_name = task_name


def create_task(magic_bucket, s3_object):
    """Creates a task for the given s3 object."""
    task_name = s3_object.key
    while True:
        dirname = os.path.dirname(task_name)
        if dirname == "":
            break
        else:
            task_name = dirname
    if task_name == "pdal-translate":
        return PdalTranslate(magic_bucket, s3_object)
    elif task_name == "rimtatls":
        return Rimtatls(magic_bucket, s3_object)
    else:
        raise UnknownTask(task_name)
