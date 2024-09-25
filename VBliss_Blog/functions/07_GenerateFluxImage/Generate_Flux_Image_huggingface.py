import os
import boto3
from botocore.exceptions import ClientError
import base64
import io
import json
import uuid
import logging
import traceback
import requests
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secret(secret_name, region_name):
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        raise e
    # Return the secret string directly
    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']
    else:
        # In case the secret is binary
        return get_secret_value_response['SecretBinary']

def get_s3_client(region_name):
    return boto3.client('s3', region_name=region_name)

def upload_image_to_s3(image_bytes, bucket_name, region_name):
    with io.BytesIO(image_bytes) as buffer:
        image = Image.open(buffer)
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        filename = f"flux_image_{uuid.uuid4()}.png"
        s3_client = get_s3_client(region_name)
        s3_client.upload_fileobj(output_buffer, bucket_name, filename)
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"

def lambda_handler(event, context):
    prompt = json.loads(event['body'])
    region_name = os.environ['REGION']
    bucket_name = os.environ['S3_BUCKET_NAME']
    token = get_secret(os.environ['SECRET'], region_name)
    API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-dev"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"inputs": prompt}
    s3_url = ""

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        s3_url = upload_image_to_s3(response, bucket_name, region_name)
        
        return {
            'statusCode': 200,
            'body': s3_url
        }
    
    except Exception as e:
        logger.error(f"Failed to process request: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise e