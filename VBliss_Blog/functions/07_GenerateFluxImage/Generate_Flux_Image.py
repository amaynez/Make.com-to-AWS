"""
This script is part of the VBliss_Blog application and is responsible for generating
images using the FLUX.1-dev model from Hugging Face. It's designed to run as an AWS
Lambda function, taking a text prompt as input and returning a URL to the generated
image stored in an S3 bucket.

Key functionalities:
1. Retrieves secrets from AWS Secrets Manager
2. Generates an image using the FLUX.1-dev model
3. Checks if the generated image is valid and not a default image
4. Uploads the generated image to an S3 bucket
5. Returns the URL of the uploaded image

The script handles errors and includes checks to ensure the generated image is not
a default "robot" image that sometimes occurs when the model fails to generate a
proper image based on the input prompt.
"""

import os
import boto3
from botocore.exceptions import ClientError
from PIL import Image
from huggingface_hub import InferenceClient
import io
import uuid
from urllib.parse import urlparse
import hashlib

def get_image_from_s3(object_key, bucket_name='vbliss-blog-img', region_name='us-west-2'):
    # Retrieve an image from an S3 bucket.
    s3 = boto3.client('s3', region_name=region_name)

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        image_content = response['Body'].read()
        return image_content
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"Error code: {error_code}")
        print(f"Error message: {error_message}")
        if error_code == 'NoSuchBucket':
            raise Exception(f"The S3 bucket '{bucket_name}' does not exist in region {region_name}.")
        elif error_code == 'NoSuchKey':
            raise Exception(f"The object '{object_key}' does not exist in bucket '{bucket_name}'.")
        else:
            raise Exception(f"Error retrieving image from S3: {str(e)}")
        
def is_default_image(image):
    """
    Check if the generated image is one of the default images.
    
    Args:
        image (PIL.Image): The generated image to check.
    
    Returns:
        bool: True if it's the default image, False otherwise.
    """
    # Calculate image hash
    image_hash = hashlib.md5(image.tobytes()).hexdigest()

    default_images = ['flux_image_default_1.png']

    # Compare with known hash of the robot image
    for default_image in default_images:
        image_data = get_image_from_s3(default_image)
        default_image_hash = hashlib.md5(image_data).hexdigest()
        print(f"Comparing image hash: {image_hash} with default image hash: {default_image_hash}")
        if image_hash == default_image_hash:
            return True


def get_secret(secret_name, region_name):
    # Retrieve a secret from AWS Secrets Manager.
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

def lambda_handler(event, context):
    # Get the input content from the event
    flux_prompt = event.get("FluxPromptOut", {}).get('body', '').strip()

    # Retrieve environment variables
    secret_name = os.environ['SECRET']
    region_name = os.environ['REGION']
    bucket_name = os.environ['S3_BUCKET_NAME']
    
    try:
        # Retrieve the secret (Hugging Face API token)
        secret_string = get_secret(secret_name, region_name)
        
        # Initialize the Hugging Face Inference Client
        client = InferenceClient(model="black-forest-labs/FLUX.1-dev", token=secret_string)
        
        # Generate the image using the FLUX model
        image = client.text_to_image(flux_prompt)
        
        # Validate the generated image
        if not isinstance(image, Image.Image) or image.width == 0 or image.height == 0:
            raise ValueError("Invalid image generated")
        
        # Check if the generated image is the default "robot" image
        if is_default_image(image):
            raise ValueError("Default robot image was generated. Retrying or aborting.")
        
        # Prepare the image for upload to S3
        with io.BytesIO() as buffer:
            image.save(buffer, format="PNG")
            buffer.seek(0)
            
            # Generate a unique filename for the image
            filename = f"flux_image_{uuid.uuid4()}.png"
            
            # Upload the image to S3
            s3_client = boto3.client('s3', region_name=region_name)
            s3_client.upload_fileobj(buffer, bucket_name, filename)
        
        # Construct the S3 URL for the uploaded image
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"
        
        # Return the S3 URL of the generated image
        return {
            'statusCode': 200,
            'body': s3_url
        }
    except Exception as e:
        # Log any unexpected errors
        print(f"Caught unexpected error: {str(e)}")
        raise e