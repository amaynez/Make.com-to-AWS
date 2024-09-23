import boto3
import os

"""
This Lambda function empties an S3 bucket specified by an environment variable.
Its main purpose is to make sure that this bucket which is used for temporary storage of blog assets,
is emptied to avoid incurring high storage costs.

Purpose:
- Deletes all objects within a specified S3 bucket
- Useful for cleanup operations or resetting bucket contents

Requirements:
- AWS Lambda execution role with permissions to list and delete objects in the specified S3 bucket
- S3_BUCKET_NAME environment variable set with the target bucket name

Note: Use with caution as this will permanently delete all objects in the bucket.
"""

def lambda_handler(event, context):
    # Initialize the S3 client
    s3 = boto3.client('s3')
    
    # Get the bucket name from environment variables
    # Ensure this is set in the Lambda function configuration
    bucket_name = os.environ['S3_BUCKET_NAME']
    
    try:
        # Create a paginator for listing objects
        # This allows handling buckets with a large number of objects
        paginator = s3.get_paginator('list_objects_v2')
        
        # Iterate through all objects and delete them
        for page in paginator.paginate(Bucket=bucket_name):
            if 'Contents' in page:
                # Prepare a list of objects to delete
                objects_to_delete = [{'Key': obj['Key']} for obj in page['Contents']]
                
                # Delete the batch of objects
                # Note: This operation is not atomic, individual deletes may fail
                s3.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})

        # Return a success response
        return {
            'statusCode': 200,
            'body': f"Bucket {bucket_name} has been emptied successfully."
        }
    
    except Exception as e:
        # Catch and re-raise any exceptions with a custom error message
        raise Exception(f"Error emptying bucket: {str(e)}")

# Note: Consider adding logging statements for better observability
# and error tracking in a production environment.
