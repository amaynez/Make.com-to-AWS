"""
Lambda function for generating images using the FLUX model and uploading them to S3.

This function:
1. Receives a prompt as input through an API Gateway event.
2. Retrieves necessary configuration from environment variables and AWS Systems Manager Parameter Store.
3. Uses the Hugging Face Inference API to generate an image based on the provided prompt.
4. Uploads the generated image to an S3 bucket.
5. Returns the S3 URL of the uploaded image.

Environment variables required:
- REGION: AWS region
- S3_BUCKET_NAME: Name of the S3 bucket to store images
- MODEL_ID: Hugging Face model ID for FLUX
- PARAMETER_NAME: Name of the parameter in AWS Systems Manager Parameter Store containing the Hugging Face API token

Error handling:
- Logs detailed error information for debugging purposes.
- Raises exceptions to be handled by AWS Lambda for appropriate error responses.
"""

import os
import boto3
import io
import json
import uuid
import logging
from PIL import Image
from huggingface_hub import InferenceClient
from botocore.exceptions import ClientError

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_parameter(parameter_name, region_name):
    ssm_client = boto3.client('ssm', region_name=region_name)
    try:
        response = ssm_client.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        logger.error(f"Error retrieving parameter: {e}")
        raise

def upload_image_to_s3(image, bucket_name, region_name):
    s3_client = boto3.client('s3', region_name=region_name)
    filename = f"flux_image_{uuid.uuid4()}.png"
    with io.BytesIO() as output:
        image.save(output, format="PNG")
        output.seek(0)
        s3_client.upload_fileobj(output, bucket_name, filename)
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"

def lambda_handler(event, context):
    try:
        prompt = json.loads(event['body'])
        region_name = os.environ['REGION']
        bucket_name = os.environ['S3_BUCKET_NAME']
        model_id = os.environ['MODEL_ID']
        token = get_parameter(os.environ['PARAMETER_NAME'], region_name)

        client = InferenceClient(model=model_id, token=token)
        image = client.text_to_image(prompt)

        if not isinstance(image, Image.Image) or image.width == 0 or image.height == 0:
            raise ValueError("Invalid image generated")

        s3_url = upload_image_to_s3(image, bucket_name, region_name)
        
        return {'statusCode': 200, 'body': s3_url}
    
    except Exception as e:
        logger.error(f"Failed to process request: {str(e)}", exc_info=True)
        raise Exception(f"Error: {str(e)}") from e