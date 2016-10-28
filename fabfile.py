from fabric.api import task, local

DOCKER_TAGS = {
        "pdal-translate": {
            "local": "gadomski/pdal-translate",
            "registry": "605350515131.dkr.ecr.us-east-1.amazonaws.com/pdal-translate:latest",
            }
        }
LAMBDA_ZIP = "build/lambda.zip"
LAMBDA_ZIP_URL = "fileb://{}".format(LAMBDA_ZIP)

@task
def create_lambda():
    zip_lambda()
    local("aws lambda create-function --function-name magic-bucket --runtime python2.7 --role arn:aws:iam::605350515131:role/magic-bucket-lambda --handler lambda.main --zip-file {}".format(LAMBDA_ZIP_URL))

@task
def update_lambda():
    zip_lambda()
    local("aws lambda update-function-code --function-name magic-bucket --zip-file {}".format(LAMBDA_ZIP_URL))

@task
def register_task_definition(name):
    local("aws ecs register-task-definition --cli-input-json file://{}/task.json".format(name))

@task
def create_sqs_queue():
    local("aws sqs create-queue --queue-name magic-bucket")

@task
def update_pdal_translate():
    update_docker("pdal-translate")

@task
def update_docker(name):
    tags = DOCKER_TAGS[name]
    docker_build(name, tags["local"])
    docker_tag(tags["local"], tags["registry"])
    docker_push(tags["registry"])

@task
def docker_build(directory, tag=None):
    if tag is None:
        tag = DOCKER_TAGS[directory]["local"]
    local("docker build -t {} {}".format(tag, directory))

@task
def docker_tag(lhs, rhs):
    local("docker tag {} {}".format(lhs, rhs))

@task
def docker_push(tag):
    local("docker push {}".format(tag))

def zip_lambda():
    local("mkdir -p build")
    local("zip -j {} lambda.py".format(LAMBDA_ZIP))
