# Magic bucket

An AWS S3 bucket that uses Docker containers to process files.

## Overview

The S3 container is `s3://crrel-magic-bucket`.
Top-level directories in the bucket define the **tasks** that are available.
As of this writing, only one task is available: `pdal-translate`.
Each task has its own workflow and data organization expectations.

## Task: pdal-translate

The `pdal-translate` task takes an input file and produces and output file, optionally applying filters and other modifications along the way.
The input file can be uploaded one of two ways:

- As a point cloud file. e.g. a file with an `.las` extension.
- As a gzipped (`.gz`) or zipped (`.zip`) archive, in which case the archive will be expanded before processing.

The configuration file is JSON.
`pdal-translate` looks for a configuration file in the following order:

1. On the filesystem.
   If you include a `config.json` in your gzipped or zipped archive, that configuration file will be used.
2. Alongside the input file, with a `.json` extension.
   E.g. if the input file is named `simple.las`, the configuration file would be named `simple.las.json` and located alongside the file in the same bucket.
3. As a directory-wide `config.json` file.
   E.g. if the input file is located at `s3://crrel-magic-bucket/pdal-translate/to-laz/simple.las`, the config file is named `s3://crrel-magic-bucket/pdal-translate/to-laz/config.json`.

Configuration files should be in the following format (all field are optional):

```js
{
  "filters": [], // a list of filters to be applied by `pdal translate`
  "output_ext": ".laz", // the extension of the output file (used to specify format)
  "args": ["--writers.las.scale_x", ".1"] // additional arguments to pass to `pdal translate`
}
```
