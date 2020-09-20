import os
import inspect
import pickle
import boto3

# s3://mlad-pipeline/onetop21/test/prepare-[TASK-ID].pkl

BUCKET = 'mlad-pipeline'
USERNAME = os.environ.get("USERNAME")
PROJECT = os.environ.get("PROJECT")
SERVICE = os.environ.get("SERVICE")
FETCH_ID = os.environ.get("FETCH_ID", "UNKNOWN")
TASK_ID = os.environ.get("TASK_ID", "UNKNOWN")

BASE_URI = f's3://{BUCKET}'
PROJECT_PATH = f'{USERNAME}/{PROJECT}'
FETCH_KEY = f'{SERVICE}-{FETCH_ID}'
SUBMIT_KEY = f'{SERVICE}-{TASK_ID}'
DATA_FORMAT = 'pkl'

def fetch(*args, **kwargs):
    if FETCH_KEY:
        print(f'Fetch : {BASE_URI}/{PROJECT_PATH}/{FETCH_KEY}.{DATA_FORMAT}')

        s3 = boto3.resource('s3', endpoint_url=os.environ.get('BOTO3_HOST'))
        bucket = s3.Bucket(BUCKET)
        if not bucket in s3.buckets.all(): bucket.create()
        obj = bucket.Object(f'{PROJECT_PATH}/{FETCH_KEY}.{DATA_FORMAT}')
        try:
            return pickle.loads(obj.get()['Body'].read())
        except:
            print(f'Failed to fetch data from {BASE_URI}/{PROJECT_PATH}/{FETCH_KEY}.{DATA_FORMAT}')
    return [], {}

def submit(*args, **kwargs):
    print(f'Submit : {BASE_URI}/{PROJECT_PATH}/{SUBMIT_KEY}.{DATA_FORMAT}')

    s3 = boto3.resource('s3', endpoint_url=os.environ.get('BOTO3_HOST'))
    bucket = s3.Bucket(BUCKET)
    if not bucket in s3.buckets.all(): bucket.create()
    obj = bucket.Object(f'{PROJECT_PATH}/{SUBMIT_KEY}.{DATA_FORMAT}')
    obj.put(Body=pickle.dumps((args, kwargs)))

def task(func):
    def wrapper(*args, **kwargs):
        # Fetch
        if not args and not kwargs:
            _args, _kwargs = fetch()
            args += _args
            kwargs.update(_kwargs)

        # Call
        result = func(*args, **kwargs)

        # Submit
        if isinstance(result, dict):
            submit(**result)
        elif isinstance(result, list) or isinstance(result, tuple):
            submit(*result)
        else:
            submit(result)

        return result

    return wrapper
