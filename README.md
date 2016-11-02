# Magic bucket

An AWS S3 bucket that uses a Docker container to process pointcloud files.
Notifications from the magic bucket are posted to the `#magic-bucket` channel in our Slack.

## Usage

The S3 container is `s3://crrel-magic-bucket`.
Top-level directories in the bucket define the tasks that are available.
Each task has its own workflow and data organization expectations, described below.

### Task: `pdal-translate`

#### Usage

```bash
aws s3 cp config.json s3://crrel-magic-bucket/pdal-translate/my-task/config.json
aws s3 cp infile.las s3://crrel-magic-bucket/pdal-translate/my-task/infile.las
# wait for the task to complete
aws s3 cp s3://crrel-magic-bucket/pdal-translate/my-task/output/infile.las outfile.las
```

The magic bucket will download `infile.las`, read configuration from `config.json`, and run everything through `pdal translate`.
The output file will be uploaded to `s3://crrel-magic-bucket/pdal-translate/my-task/output/infile.las`.

#### Detail

The `pdal-translate` task takes an input file and produces and output file, optionally applying filters and other modifications along the way.
The input file can be uploaded one of two ways:

- As a point cloud file. e.g. a file with an `.las` extension.
- As a gzipped (`.gz`) or zipped (`.zip`) archive, in which case the archive will be expanded before processing.

The configuration file is JSON.
`pdal-translate` looks for a configuration file in the following order:

1.  If you include a `config.json` in your gzipped or zipped archive, that configuration file will be used.
2. If the input file is `s3://crrel-magic-bucket/pdal-translate/to-laz/simple.las`, the configuration file is named `s3://crrel-magic-bucket/pdal-translate/to-laz/simple.las.json`.
3. If the input file is `s3://crrel-magic-bucket/pdal-translate/to-laz/simple.las`, the configuration file is named `s3://crrel-magic-bucket/pdal-translate/to-laz/config.json`.

Configuration files look like this (all fields optional):

```js
{
  "filters": [], // a list of filters to be applied by `pdal translate`
  "output_ext": ".laz", // the extension of the output file (used to specify format)
  "args": ["--writers.las.scale_x", ".1"] // additional arguments to pass to `pdal translate`
}
```

See the examples directory in this repo for sample configuration files.


### Task: `rimtatls`

Runs Riegl's `rimtatls` executable on `rxp` files:

```
aws s3 cp 160520_181202.rxp s3://crrel-magic-bucket/rimtatls/160520_181202.rxp
aws s3 cp s3://crrel-magic-bucket/rimtatls/output/160520_181202.mta.rxp 160520_181202.mta.rxp
```

An `.mta` is inserted into the filename to indicate that it has been MTA processed.

## Architecture

The magic bucket consists of these parts:

- An S3 bucket called `crrel-magic-bucket`.
- An AWS lambda function, called `magic-bucket`, whose code lives in `lambda.py`.
  This function takes an S3 event and does two things:
    1. Puts a message into an SQS queue, called `magic-bucket`, containing the contents of the S3 event.
    2. Starts an ECS task, called `magic-bucket`, to process all messages in SQS queue.
- An ECS task, called `magic-bucket`, that runs a Docker container, called `magic-bucket`.
  The docker container is built with `docker/Dockerfile` and runs the code in `docker/main.py`.
