from fabric.api import task, local

LOCAL_DOCKER_TAG = "gadomski/magic-bucket"
REGISTRY_DOCKER_TAG = "605350515131.dkr.ecr.us-east-1.amazonaws.com/magic-bucket:latest"
LAMBDA_ZIP = "build/lambda.zip"
LAMBDA_ZIP_URL = "fileb://{}".format(LAMBDA_ZIP)


@task
def update_lambda():
    local("mkdir -p build")
    local("zip -j {} lambda.py".format(LAMBDA_ZIP))
    local("aws lambda update-function-code --function-name magic-bucket --zip-file {}".format(LAMBDA_ZIP_URL))


@task
def register_task_definition():
    local("aws ecs register-task-definition --cli-input-json file://task-definition.json")


@task
def update_docker(slack_token):
    docker_build(slack_token, LOCAL_DOCKER_TAG)
    docker_tag(LOCAL_DOCKER_TAG, REGISTRY_DOCKER_TAG)
    docker_push(REGISTRY_DOCKER_TAG)


@task
def docker_build(slack_token, tag):
    local("docker build -t {} --build-arg SLACK_TOKEN={} docker".format(tag, slack_token))


@task
def docker_tag(lhs, rhs):
    local("docker tag {} {}".format(lhs, rhs))


@task
def docker_push(tag):
    local("docker push {}".format(tag))
