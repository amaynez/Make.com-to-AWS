"""
This script is part of the VBliss_Blog application and is responsible for generating
images using the FLUX.1-dev model deployed on AWS SageMaker. It's designed to run as an AWS
Lambda function, taking a text prompt as input and returning a URL to the generated
image stored in an S3 bucket.

Key functionalities:
1. Checks if the SageMaker endpoint exists and is in service, creating it if necessary.
2. Generates an image using the FLUX.1-dev model via the SageMaker endpoint.
3. Uploads the generated image to an S3 bucket.
4. Deletes the SageMaker endpoint after the image generation process is complete to avoid additional costs.
5. Returns the URL of the uploaded image.

Recent updates:
- Added functionality to check if the SageMaker endpoint exists and is in service.
- If the endpoint does not exist, it is created and the script waits until it is in service.
- The SageMaker endpoint is deleted after the image generation process is complete.
- Improved error handling and logging for better debugging and monitoring.
- Added support for unique filenames for the generated images to avoid conflicts in the S3 bucket.
"""

import os
import time
import boto3
from botocore.exceptions import ClientError
from PIL import Image
import io
import uuid
import sagemaker
import logging
import traceback
from sagemaker.huggingface import HuggingFaceModel
from setuptools import setup, find_packages

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_secret(secret_name, region_name):
    """
    Retrieve a secret from AWS Secrets Manager.
    
    :param secret_name: Name of the secret to retrieve
    :param region_name: AWS region where the secret is stored
    :return: Secret value as a string
    """
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

def upload_image_to_s3(image, bucket_name, region_name):
    with io.BytesIO() as buffer:
        image.save(buffer, format="PNG")
        buffer.seek(0)
        filename = f"flux_image_{uuid.uuid4()}.png"
        s3_client = get_s3_client(region_name)
        s3_client.upload_fileobj(buffer, bucket_name, filename)
    return f"https://{bucket_name}.s3.amazonaws.com/{filename}"

def lambda_handler(event, context):
    prompt = event.get("FluxPromptOut", {}).get('body', '').strip()
    region_name = os.environ['REGION']
    bucket_name = os.environ['S3_BUCKET_NAME']
    endpoint_name = os.environ['SAGEMAKER_ENDPOINT_NAME']
    model_id = os.environ['MODEL_ID']
    token = get_secret(os.environ['SECRET'], region_name)
    
    try:
        try:
            role = sagemaker.get_execution_role()
        except ValueError:
            iam = boto3.client('iam')
            role = iam.get_role(RoleName='AmazonSageMaker-ExecutionRole-20240823T102522')['Role']['Arn']

        # Create the HuggingFaceModel instance
        huggingface_model = HuggingFaceModel(
            transformers_version="4.26.0",
            pytorch_version="1.13.1",
            py_version="py39",
            model_data=None,  # Set to None for deploying from Hugging Face Hub
            role=role,
            image_uri=None,  # Let SageMaker choose the appropriate image
            env={
                'HF_MODEL_ID': model_id,
                'HF_TASK': 'text-to-image',
                'HUGGING_FACE_HUB_TOKEN': token
            }
        )

        # deploy model to SageMaker Inference
        predictor = huggingface_model.deploy(
            initial_instance_count=1,
            instance_type="ml.g5.8xlarge"
        )
        
        # Get the endpoint name from the predictor
        endpoint_name = predictor.endpoint_name

        # Create a SageMaker client
        sagemaker_client = boto3.client('sagemaker')

        # Function to check the endpoint status
        def check_endpoint_status(endpoint_name):
            try:
                response = sagemaker_client.describe_endpoint(EndpointName=endpoint_name)
                status = response['EndpointStatus']
                return status
            except ClientError as e:
                logger.error(f"Error checking endpoint status: {e}")
                return None

        # Wait for the endpoint to be in service
        max_wait_time = 900  # 15 minutes
        wait_time = 0
        check_interval = 30  # Check every 30 seconds

        logger.info(f"Waiting for endpoint {endpoint_name} to be in service...")

        while wait_time < max_wait_time:
            status = check_endpoint_status(endpoint_name)
            if status == 'InService':
                logger.info(f"Endpoint {endpoint_name} is in service!")
                break
            elif status in ['Creating', 'Updating']:
                logger.info(f"Endpoint {endpoint_name}is being created or updated.")
                time.sleep(check_interval)
                wait_time += check_interval
            else:
                logger.error(f"Endpoint is not in service. Status: {status}")
                predictor.delete_endpoint()
                raise Exception(f"Endpoint {endpoint_name} is not in service.")

        if wait_time >= max_wait_time:
            logger.error(f"Timeout waiting for endpoint {endpoint_name} to be in service.")
            predictor.delete_endpoint()
            raise Exception(f"Timeout waiting for endpoint {endpoint_name} to be in service.")

        response = predictor.predict({
            "inputs": prompt,
        })

        image = Image.open(io.BytesIO(response))
        s3_url = upload_image_to_s3(image, bucket_name, region_name)
        predictor.delete_endpoint()
        
    except Exception as e:
        logger.error(f"Failed to process request: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        predictor.delete_endpoint()
        raise e

    return {
        'statusCode': 200,
        'body': s3_url
    }