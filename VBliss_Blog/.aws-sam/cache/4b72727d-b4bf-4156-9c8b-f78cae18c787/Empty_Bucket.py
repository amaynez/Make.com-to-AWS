import boto3
import os

def lambda_handler(event, context):
    # Initialize the S3 client
    s3 = boto3.client('s3')
    
    # Get the bucket name from environment variables
    bucket_name = os.environ['S3_BUCKET_NAME']
    
    try:
        # List all objects in the bucket
        paginator = s3.get_paginator('list_objects_v2')
        
        # Iterate through all objects and delete them
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})

        return {
            'statusCode': 200,
            'body': f"Bucket {bucket_name} has been emptied successfully."
        }
    
    except Exception as e:
        raise Exception(f"Error emptying bucket: {str(e)}")
