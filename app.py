import os

from aws_cdk import (
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_lambda_event_sources as sources,
    aws_sqs as sqs,
    aws_s3 as s3,
    aws_s3_assets,
    core
)


class DomainScanStack(core.Stack):
    def __init__(self, app: core.App, id: str) -> None:
        super().__init__(app, id)

        ##################################
        # Lambda Timeouts (seconds) & Queue Redrive
        ##################################
        
        lambda_gatherer_timeout = 600
        lambda_joiner_timeout = 350
        # pa11y's timeout is set to 50, so the lambda is just a little longer
        lambda_a11y_scan_timeout = 55
        max_receive_count = 2
        
        ##################################
        # S3 Bucket with Domains
        ##################################

        asset = aws_s3_assets.Asset(
            self, 'domain-list',
            path=os.path.abspath('./domains/domains.csv')
        )
        
        ##################################
        # Domain Gatherer Lambda and Queue
        ##################################

        domain_queue = sqs.Queue(
            self, 'domain-queue',
            visibility_timeout=core.Duration.seconds(
                (max_receive_count + 1) * lambda_gatherer_timeout),
            dead_letter_queue=sqs.DeadLetterQueue(
                max_receive_count=max_receive_count,
                queue=sqs.Queue(
                    self, 'domain-queue-dlq',
                    retention_period=core.Duration.days(5)
                )
            )
        )
        
        lambda_gatherer = lambda_.Function(
            self, "domain-gatherer",
            code=lambda_.Code.from_asset('./lambdas/domain_gatherer'),
            handler="handler.main",
            timeout=core.Duration.seconds(lambda_gatherer_timeout),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=150
        )

        lambda_gatherer.add_environment('SQS_URL', domain_queue.queue_url)
        lambda_gatherer.add_environment('BUCKET_NAME', asset.s3_bucket_name)
        lambda_gatherer.add_environment('OBJECT_KEY', asset.s3_object_key)
        
        lambda_gatherer_sqs_exec_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=['lambda:InvokeFunction', 
                     'sqs:SendMessage', 
                     'sqs:DeleteMessage', 
                     'sqs:SendMessageBatch',
                     'sqs:SetQueueAttributes',
                     'sqs:GetQueueAttributes',
                     'sqs:GetQueueUrl',
                     'sqs:GetQueueAttributes'],
            resources=[
                domain_queue.queue_arn
            ]
        )
        lambda_gatherer.add_to_role_policy(lambda_gatherer_sqs_exec_policy)
        domain_queue.grant_send_messages(lambda_gatherer)
        
        # trigger for 1st and 15th of the month at 18:00 UTC (1pm EST)
        lambda_gatherer_rule = events.Rule(
            self, "Lambda Gatherer Rule",
            schedule=events.Schedule.cron(
                minute='0',
                hour='18',
                day="1,15",
                month='*',
                year='*'
            )
        )
        lambda_gatherer_rule.add_target(
            targets.LambdaFunction(lambda_gatherer)
        )
        asset.grant_read(lambda_gatherer)

        ##################################
        # A11y Scanner Lambda and S3
        ##################################

        layer = lambda_.LayerVersion(
            self, 'chrome-aws-lambda',
            code=lambda_.Code.from_asset('./lambdas/chrome_aws_lambda.zip'),
            compatible_runtimes=[lambda_.Runtime.NODEJS_10_X],
            description='A layer of chrome-aws-lambda'
        )

        lambda_a11y_scan = lambda_.Function(
            self, "a11y-scan",
            code=lambda_.Code.from_asset('./lambdas/a11y_scan'),
            handler="index.handler",
            timeout=core.Duration.seconds(lambda_a11y_scan_timeout),
            runtime=lambda_.Runtime.NODEJS_10_X,
            memory_size=1000,
            layers=[layer]
        )

        lambda_a11y_scan.add_event_source(
            sources.SqsEventSource(domain_queue, batch_size=1)
        )
        
        # create s3 bucket to put results
        results_bucket = s3.Bucket(
            self, 'results-bucket',
            versioned=False,
            removal_policy=core.RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                ignore_public_acls=True,
                block_public_policy=True,
                restrict_public_buckets=True
            ),
            lifecycle_rules=[
                s3.LifecycleRule(
                    enabled=True,
                    expiration=core.Duration.days(10)
                )
            ]
        )

        lambda_a11y_scan.add_environment(
            'BUCKET_NAME',
            results_bucket.bucket_name
        )
        results_bucket.grant_put(lambda_a11y_scan)

        ##################################
        # Results Joiner Lambda
        ##################################

        # create s3 bucket to put site data
        data_bucket = s3.Bucket(
            self, 'data-bucket',
            versioned=False,
            removal_policy=core.RemovalPolicy.DESTROY,
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=True,
                ignore_public_acls=True,
                block_public_policy=True,
                restrict_public_buckets=True
            )
        )

        lambda_joiner = lambda_.Function(
            self, "results-joiner",
            code=lambda_.Code.from_asset('./lambda-releases/results_joiner.zip'),
            handler="handler.main",
            timeout=core.Duration.seconds(lambda_joiner_timeout),
            runtime=lambda_.Runtime.PYTHON_3_7,
            memory_size=400
        )
        lambda_joiner.add_environment(
            'DATA_BUCKET_NAME',
            data_bucket.bucket_name
        )
        lambda_joiner.add_environment(
            'RESULTS_BUCKET_NAME',
            results_bucket.bucket_name
        )
        results_bucket.grant_read_write(lambda_joiner)
        data_bucket.grant_read_write(lambda_joiner)

        # trigger for 8th and 23rd of the month at 18:00 UTC (1pm EST)
        lambda_joiner_rule = events.Rule(
            self, "Lambda Joiner Rule",
            schedule=events.Schedule.cron(
                minute='0',
                hour='18',
                day="8,23",
                month='*',
                year='*'
            )
        )
        lambda_joiner_rule.add_target(targets.LambdaFunction(lambda_joiner))
        

app = core.App()
DomainScanStack(app, "DomainScanStack")
app.synth()
