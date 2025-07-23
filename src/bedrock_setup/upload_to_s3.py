import os
import logging
import boto3
from botocore.exceptions import ClientError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('s3_uploader')

def upload_file_to_s3(file_path, bucket, object_name=None, content_type=None):
    """Upload a file to an S3 bucket

    :param file_path: File to upload
    :param bucket: Bucket to upload to
    :param object_name: S3 object name. If not specified file_name is used
    :param content_type: Content type of the file
    :return: True if file was uploaded, else False
    """

    # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_path)

    # Upload the file
    s3_client = boto3.client('s3')
    try:
        extra_args = {}
        if content_type:
            extra_args['ContentType'] = content_type

        s3_client.upload_file(
            file_path,
            bucket,
            object_name,
            ExtraArgs=extra_args
        )
        logger.info(f"Uploaded {file_path} to s3://{bucket}/{object_name}")
        return True
    except ClientError as e:
        logger.error(f"Upload failed: {e}")
        return False

def upload_directory_to_s3(directory, bucket, prefix="", content_type_mapping=None):
    """Upload an entire directory to an S3 bucket with an optional prefix

    :param directory: Local directory to upload
    :param bucket: Bucket to upload to
    :param prefix: Prefix to add to object names in S3
    :param content_type_mapping: Dictionary mapping file extensions to content types
    :return: True if all files were uploaded successfully, else False
    """
    if not os.path.isdir(directory):
        logger.error(f"Directory does not exist: {directory}")
        return False

    if content_type_mapping is None:
        # Default content type mapping for common documentation formats
        content_type_mapping = {
            '.md': 'text/markdown',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.html': 'text/html',
            '.pdf': 'application/pdf',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.svg': 'image/svg+xml',
        }

    success = True
    for root, _, files in os.walk(directory):
        for file in files:
            local_path = os.path.join(root, file)

            # Calculate relative path from the directory
            relative_path = os.path.relpath(local_path, directory)

            # Construct S3 object name with prefix
            s3_path = os.path.join(prefix, relative_path).replace('\\', '/')

            # Determine content type based on file extension
            _, ext = os.path.splitext(file)
            content_type = content_type_mapping.get(ext.lower())

            # Upload file
            if not upload_file_to_s3(local_path, bucket, s3_path, content_type):
                success = False

    return success

def check_bucket_exists(bucket_name):
    """Check if an S3 bucket exists and is accessible

    :param bucket_name: Name of the bucket to check
    :return: True if the bucket exists and is accessible, else False
    """
    s3_client = boto3.client('s3')
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            logger.error(f"Bucket {bucket_name} does not exist")
        elif error_code == '403':
            logger.error(f"Access to bucket {bucket_name} is forbidden")
        else:
            logger.error(f"Error checking bucket {bucket_name}: {e}")
        return False

def create_bucket_if_not_exists(bucket_name, region=None):
    """Create an S3 bucket if it does not exist

    :param bucket_name: Name of the bucket to create
    :param region: AWS region to create the bucket in
    :return: True if the bucket exists or was created successfully, else False
    """
    # Check if bucket already exists
    if check_bucket_exists(bucket_name):
        logger.info(f"Bucket {bucket_name} already exists")
        return True

    # Create the bucket
    s3_client = boto3.client('s3')
    try:
        if region is None or region == 'us-east-1':
            # us-east-1 is the default region and requires special handling
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            location = {'LocationConstraint': region}
            s3_client.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration=location
            )

        logger.info(f"Created bucket {bucket_name}")
        return True
    except ClientError as e:
        logger.error(f"Failed to create bucket {bucket_name}: {e}")
        return False

def upload_documentation(base_dir, bucket_name, key_prefix="dbkb"):
    """Upload all documentation to S3

    :param base_dir: Base directory containing the docs directory
    :param bucket_name: S3 bucket name
    :param key_prefix: Prefix to add to S3 keys
    :return: True if upload was successful, else False
    """
    # Path to documentation directories
    schema_dir = os.path.join(base_dir, 'docs', 'schema')
    queries_dir = os.path.join(base_dir, 'docs', 'queries')

    # Check if bucket exists or create it
    if not check_bucket_exists(bucket_name):
        logger.warning(f"Bucket {bucket_name} does not exist or is not accessible")
        return False

    # Upload schema documentation
    if os.path.isdir(schema_dir):
        logger.info(f"Uploading schema documentation to s3://{bucket_name}/{key_prefix}/schema/")
        schema_success = upload_directory_to_s3(
            schema_dir,
            bucket_name,
            f"{key_prefix}/schema/"
        )
        if not schema_success:
            logger.error("Failed to upload schema documentation")
    else:
        logger.warning(f"Schema documentation directory not found: {schema_dir}")
        schema_success = True  # Don't fail if directory doesn't exist

    # Upload query documentation
    if os.path.isdir(queries_dir):
        logger.info(f"Uploading query documentation to s3://{bucket_name}/{key_prefix}/queries/")
        queries_success = upload_directory_to_s3(
            queries_dir,
            bucket_name,
            f"{key_prefix}/queries/"
        )
        if not queries_success:
            logger.error("Failed to upload query documentation")
    else:
        logger.warning(f"Query documentation directory not found: {queries_dir}")
        queries_success = True  # Don't fail if directory doesn't exist

    return schema_success and queries_success

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Upload documentation to S3')
    parser.add_argument('--bucket', required=True, help='S3 bucket name')
    parser.add_argument('--prefix', default='dbkb', help='Key prefix for S3 objects')
    parser.add_argument('--dir', default=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        help='Base directory containing the docs directory')

    args = parser.parse_args()

    if upload_documentation(args.dir, args.bucket, args.prefix):
        print(f"Documentation successfully uploaded to s3://{args.bucket}/{args.prefix}/")
    else:
        print("Documentation upload failed")
        exit(1)