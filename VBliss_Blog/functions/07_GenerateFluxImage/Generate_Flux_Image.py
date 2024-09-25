"""
This Lambda function is part of the VBliss_Blog step function workflow.
It is responsible for generating an image based on a given prompt using
the Amazon Bedrock AI model and uploading the resulting image to an S3 bucket.

The function performs the following steps:
1. Receives a prompt from the previous step in the workflow
2. Invokes the Bedrock model to generate an image based on the prompt
3. Uploads the generated image to an S3 bucket
4. Returns the S3 URL of the uploaded image
"""
import os
import boto3
import base64
import json
import io
import uuid
import logging
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_s3_client():
    return boto3.client('s3', region_name=os.environ['REGION'])

def upload_image_to_s3(image_bytes):
    s3_client = get_s3_client()
    bucket_name = os.environ['S3_BUCKET_NAME']
    filename = f"flux_image_{uuid.uuid4()}.png"
    
    with io.BytesIO(image_bytes) as buffer:
        image = Image.open(buffer)
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="PNG")
        output_buffer.seek(0)
        s3_client.upload_fileobj(output_buffer, bucket_name, filename)
    
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"

def invoke_bedrock_model(prompt):
    bedrock = boto3.client('bedrock-runtime', region_name=os.environ['REGION'])
    response = bedrock.invoke_model(
        modelId=os.environ['MODEL_ID'],
        body=json.dumps({'prompt': prompt})
    )
    output_body = json.loads(response["body"].read().decode("utf-8"))
    return base64.b64decode(output_body["images"][0])

def lambda_handler(event, context):
    try:
        prompt = json.loads(event['body'])
        
        image_data = invoke_bedrock_model(prompt)
        s3_url = upload_image_to_s3(image_data)
        
        return {
            'statusCode': 200,
            'body': s3_url
        }
    
    except Exception as e:
        logger.error(f"Failed to process request: {str(e)}", exc_info=True)
        raise