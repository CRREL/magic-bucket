from fabric.api import task, local

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
def create_sqs_queue():
    local("aws sqs create-queue --queue-name magic-bucket")

def zip_lambda():
    local("mkdir -p build")
    local("zip -j {} lambda.py".format(LAMBDA_ZIP))
