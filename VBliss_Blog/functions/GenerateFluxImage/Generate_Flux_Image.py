"""
This script is a Lambda function for generating and storing AI-generated images.

It uses a Hugging Face model deployed on SageMaker to generate images based on text prompts.
The generated images are then uploaded to an S3 bucket and the URL is returned.

Key components:
1. Image generation using a Hugging Face model
2. S3 upload functionality
3. Lambda handler to process incoming requests

Environment variables required:
- S3_BUCKET_NAME: Name of the S3 bucket to store generated images
- ENDPOINT_NAME: Name of the SageMaker endpoint for the Hugging Face model
"""

import os
import boto3
from PIL import Image
import io
import uuid
import json

def generate_image(predictor, prompt):
    """
    Generate an image using the Hugging Face model predictor.
    
    :param predictor: HuggingFacePredictor instance
    :param prompt: Text prompt for image generation
    :return: PIL Image object
    """
    image_bytes = predictor.predict({"inputs": prompt})
    return Image.open(io.BytesIO(image_bytes))

def upload_to_s3(image, bucket_name):
    """
    Upload a PIL Image to S3 and return the public URL.
    
    :param image: PIL Image object
    :param bucket_name: Name of the S3 bucket
    :return: Public URL of the uploaded image
    """
    s3_client = boto3.client('s3')
    filename = f"flux_image_{uuid.uuid4()}.png"
    
    # Convert PIL Image to bytes
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Upload to S3
    s3_client.upload_fileobj(buffer, bucket_name, filename)
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    :param event: Lambda event object
    :param context: Lambda context object
    :return: Dictionary with statusCode and body (S3 URL of the generated image)
    """
    # Extract the prompt from the event
    flux_prompt = event.get("FluxPromptOut", {}).get('body', '').strip()
    
    # Get environment variables
    bucket_name = os.environ['S3_BUCKET_NAME']
    endpoint_name = os.environ['ENDPOINT_NAME']

    try:
        # Initialize the SageMaker runtime client
        runtime_client = boto3.client('sagemaker-runtime')
        
        # Generate the image
        image = generate_image(runtime_client, endpoint_name, flux_prompt)
        
        # Upload the image to S3
        s3_url = upload_to_s3(image, bucket_name)

        return {'statusCode': 200, 'body': s3_url}
    except Exception as e:
        print(f"Caught unexpected error: {str(e)}")
        raise