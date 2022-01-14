from os import environ as env
import sys

import boto3
from botocore.exceptions import ClientError


def get_env_var(name):
    """Get the environment variable `name` from environment variable.

    Return the value of the `name` env var if found, None otherwise.
    """
    try:
        env_var = env[name]
    except KeyError as ke:
        print(f'Could not get env. var. "{ke}". Make sure it is set')
        sys.exit(1)
    else:
        return env_var


def get_scaleway_s3_client():
    """Get a boto3 s3 client to use with Scaleway Object Storage."""
    SCALEWAY_ACCESS_KEY_ID = get_env_var('SCALEWAY_ACCESS_KEY_ID')
    SCALEWAY_SECRET_ACCESS_KEY = get_env_var('SCALEWAY_SECRET_ACCESS_KEY')

    # static Scaleway settings (using NL region only)
    S3_REGION_NAME = 'nl-ams'
    S3_ENDPOINT_URL = 'https://s3.nl-ams.scw.cloud'

    s3 = boto3.client('s3',
                      region_name=S3_REGION_NAME,
                      endpoint_url=S3_ENDPOINT_URL,
                      aws_access_key_id=SCALEWAY_ACCESS_KEY_ID,
                      aws_secret_access_key=SCALEWAY_SECRET_ACCESS_KEY
                      )
    return s3


def download_gnucash_file_from_scaleway_s3(object_key, dest_path, bucket_name, s3_client):
    """Download the .gnucash file from Scaleway S3 (Object Storage) to the destination path.

       The s3_client object should be created using the function called
       get_scaleway_s3_client().

       The dest_path should be set to the fully qualified path where S3 will temporarily
       store the GnuCash file.

       The bucket_name param is the name of your Scaleway Object Storage bucket.

       the object_key param  is the object key / name in Scaleway Object Storage.
    """
    try:
        s3_client.download_file(Bucket=bucket_name,
                                Key=object_key,
                                Filename=dest_path
                                )
        print(f'Successfully downloaded GnuCash file {object_key} from S3.')
        return True
    except ClientError as ce:
        if ce.response['Error']['Code'] == 'NoSuchKey':
            msg = 'Attempted to pull down GnuCash file from S3, but no such file.'
        else:
            msg = 'Attempted to pull down GnuCash file from S3, but unexpected error occurred: '
            msg += ce.response['Error']['Code'] + ' ' + ce.response['Error']['Message']
        print(msg)
        return False
    else:
        return False


def upload_gnucash_file_to_scaleway_s3(src_path, bucket_name, obj_key, s3_client):
    """Upload a GnuCash file to Scaleway Object Storage."""
    try:
        print(f'Uploading file "{src_path}" to bucket "bucket_name"')
        s3_client.upload_file(Filename=src_path, Bucket=bucket_name, Key=obj_key)
    except ClientError as ce:
        msg = 'Failed to upload GnuCash file to S3 with error: '
        msg += ce.response['Error']['Code'] + ' ' + ce.response['Error']['Message']
        print(msg)
        return False
    except FileNotFoundError:
        raise SystemExit(f'❌ File {src_path} not found. Exiting.')
    else:
        print('✅ Successfully uploaded GnuCash file to S3.')
        return True


def main():
    USAGE = 'scaleway_upload.py <BUCKET_NAME> <PATH_TO_LOCAL_GNUCASH_FILE> <FILE_NAME>'
    try:
        assert len(sys.argv) == 4
    except AssertionError:
        raise SystemExit(USAGE)
    try:
        BUCKET_NAME = sys.argv[1]
        GNUCASH_FILE_PATH = sys.argv[2]
        GNUCASH_FILE_NAME = sys.argv[3]
    except IndexError:
        raise SystemExit(USAGE)

    scaleway_s3_client = get_scaleway_s3_client()
    upload_gnucash_file_to_scaleway_s3(GNUCASH_FILE_PATH, BUCKET_NAME, GNUCASH_FILE_NAME, scaleway_s3_client)


if __name__ == '__main__':
    main()
