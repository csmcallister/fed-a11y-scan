[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![CircleCI](https://circleci.com/gh/csmcallister/fed-a11y-scan.svg?style=svg)](https://circleci.com/gh/csmcallister/fed-a11y-scan)
[![Test Coverage](https://api.codeclimate.com/v1/badges/52cc06fdf519f75d6b4c/test_coverage)](https://codeclimate.com/github/csmcallister/fed-a11y-scan/test_coverage)

# Fed A11y Scan

Automated accessibility testing of U.S. Federal Government websites using a serverless infrastructure.

>**Disclaimer**:  The scans do not constitute a complete accessibility evaluation. Due to the limitations of automated testing software, one should not take these scan results to be authoritative or to convey a Section 508 conformance assessment. Only a professional evaluator can perform a complete accessibility evaluation, often using a combination of manual and automated testing. For guidance, please refer to the [Harmonized Testing Process for Section 508 Compliance: Baseline Tests for Software and Web Accessibility](https://www.dhs.gov/sites/default/files/publications/Baseline_Tests_for_Software_and_Web_Accessibility_3.pdf).

## Getting Started

Following these steps will help you get started.

>If you're only interested in the list of Federal domains we scan, you can checkout the [spreadsheet](https://github.com/csmcallister/fed-a11y-scan/tree/master/domains/domains.csv) that has them all - at least the ones we've been able to find - as well as the [script](https://github.com/csmcallister/fed-a11y-scan/tree/master/domains/create_domains_csv.py)) used to generate that file.

### Install Docker

We use Docker to create a local AWS Linux environment, which is necessary for packaging up the lambda dependencies, such as Python's lxml library, which must be OS-aware. See how to [install Docker here](https://docs.docker.com/get-docker/).

### Install and Configure the AWS CDK

Follow the instructions [here](https://docs.aws.amazon.com/cdk/latest/guide/getting_started.html) to install and configure the AWS CDK. You'll need to install node.js as a part of this step if you don't already have it.

>You must specify your credentials and an AWS Region to use the AWS CDK CLI. There are multiple ways to do this, but our examples (and Makefile) use the `--profile` option with cdk commands. This means our credentials and region are specified in `~/.aws/config`.

### Install Python

This project uses Python 3.7.3, although other versions >= 3.5 *should* be fine. You can install Python from [here](https://www.python.org/downloads/), although using a system utility (e.g. homebrew for OSX) is fine as well.

Next, activate your python virtual environment:

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt
```

### Build

These instructions prepare assets for deployment via the AWS CDK.

#### Build a11y scan lambda

Before we let the AWS CDK deploy the a11y lambda function, we need to make a lambda layer for headless chrome and then tweak the internals of `pa11y`, the accessibility scanning tool, to use headless chrome.

To create the lamda layer with [chrome-aws-lambda](https://github.com/alixaxel/chrome-aws-lambda) and replace `pa11y`'s dependency on puppeteer with puppeteer-core, run:

```bash
make build_a11y_scan
```

The above command will install the node modules into `lambdas/a11y_scan` and create a zip archive called `chrome_aws_lambda.zip` within `/lambdas/`.

#### Build the Site Mapper

This lambda uses scrapy to sitemap each domain. In order to deploy it, we first need to make a lambda layer out of the dependencies, using Docker to make sure they're built in an AWS Linux environment:

```bash
make build_site_mapper
```

The above command will create a zip archive called `site_mapper_layer.zip` within `./lambda-releases/`.

#### Build the scan results joiner lambda

This lambda joins all of the individual scan results into one aggregate file, which will be usef the the front-end of the application. It also calculates historical trends and saves them for future reference.

To build this lambda, run:

```bash
make build_results_joiner
```

After this, you'll have a new directory in the root of the repo called `lambda_releases` with a file called `results.joiner.zip`. That is the lambda deployment package.

## Deploy

First, run the following command to see the version number of the AWS CDK:

```bash
cdk --version
```

>Note: we're working with `1.27.0`.

Now we'll use `cdk bootstrap` to create a Cloudformation stack to manage the s3 buckets for the lambda assets as well as the csv containg the domains we'll be scanning.

```bash
`cdk bootstrap --profile <your profile name>`
```

This shouldn't take too long and should finish with a message that looks something like this:

```bash
✅  Environment aws://<account id>/<your-region> bootstrapped.
```

Now we can deploy / redeploy our Stack:

```bash
`cdk deploy --profile <your profile name>`
```

After that command has finished, the resources specified in `app.py` have been deployed to the AWS account you configured with the CDK. You can now log into your AWS Console and check out all the stuff.

## Synthesize Cloudformation Template

You can optionally see the Cloudformation template generated by the CDK. To do so, run `cdk synth`, then check the output file in the "cdk.out" directory.

## Cleaning Up

You can destroy the AWS resources created by this app with `cdk destroy --profile <your profile name>`. Note that although we've given the S3 Buckets a `removalPolicy` of `cdk.RemovalPolicy.DESTROY` so that they aren't orphaned at the end of this process (you can read more about that [here](https://docs.aws.amazon.com/AmazonS3/latest/user-guide/delete-bucket.html)), they'll fail to get destroyed if they contain objects. So you should log into the console and delete all of the objects within the buckets beforehand.

Note, however, that this step will not destroy the CloudFormation Stack or the S3 bucket created by `cdk bootstrap`. There doesn't [seem](https://github.com/aws/aws-cdk/issues/986) to be a way to do this from the command line at present, so you should log into your AWS console and manually delete first the s3 bucket and then the CloudFormation Stack.

## LICENSE

GNU General Public License. See it [here](https://github.com/csmcallister/fed-a11y-scan/blob/master/.github/LICENSE).
