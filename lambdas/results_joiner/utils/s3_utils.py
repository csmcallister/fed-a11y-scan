import asyncio
import json
import logging

import aioboto3
import boto3

logger = logging.getLogger(__name__)
s3 = boto3.client("s3")


def read_object(key, bucket):
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except Exception as e:
        logger.error(e, exc_info=True)
        return
    data = json.loads(obj.get('Body').read().decode('utf-8'))
    
    return data


def put_object(data, bucket, key):
    json_obj = bytes(json.dumps(data).encode('UTF-8'))
    params = {
        'Bucket': bucket,
        'Key': key,
        'Body': json_obj,
        'ContentType': 'application/json'
    }
    try:
        s3.put_object(**params)
    except Exception as e:
        logger.error(e, exc_info=True)


def delete_object(key, bucket):
    try:
        s3.delete_object(Bucket=bucket, Key=key)
    except Exception as e:
        logger.error(e, exc_info=True)


def partial_key_exists(key, bucket):
    """Returns the full key to an object if a partial key match; else False"""
    response = s3.list_objects_v2(Bucket=bucket, Prefix=key)
    for obj in response.get('Contents', []):
        obj_key = obj['Key']
        if key in obj_key:
            return obj_key
    return False


def get_matching_s3_objects(bucket, prefix="", suffix=""):
    """
    Generate objects in an S3 bucket.
    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch objects whose key starts with
        this prefix (optional).
    :param suffix: Only fetch objects whose keys end with
        this suffix (optional).
    """
    paginator = s3.get_paginator("list_objects_v2")

    kwargs = {'Bucket': bucket}

    # We can pass the prefix directly to the S3 API.  If the user has passed
    # a tuple or list of prefixes, we go through them one by one.
    prefixes = (prefix, ) if isinstance(prefix, str) else prefix

    for key_prefix in prefixes:
        kwargs["Prefix"] = key_prefix

        for page in paginator.paginate(**kwargs):
            try:
                contents = page["Contents"]
            except KeyError:
                break

            for obj in contents:
                key = obj["Key"]
                if key.endswith(suffix):
                    yield obj


def get_matching_s3_keys(bucket, prefix="", suffix=""):
    """
    Generate the keys in an S3 bucket.
    :param bucket: Name of the S3 bucket.
    :param prefix: Only fetch keys that start with this prefix (optional).
    :param suffix: Only fetch keys that end with this suffix (optional).
    """
    for obj in get_matching_s3_objects(bucket, prefix, suffix):
        yield obj["Key"]


async def async_read_object(client, bucket, key):
    s3_ob = await client.get_object(Bucket=bucket, Key=key)
    async with s3_ob["Body"] as stream:
        file_data = await stream.read()
        data = json.loads(file_data.decode('utf-8'))
        return data


async def bulk_read(bucket, keys):
    tasks = []
    async with aioboto3.client("s3") as client:
        for key in keys:
            tasks.append(async_read_object(client, bucket, key))
        data = await asyncio.gather(*tasks)
        return data
