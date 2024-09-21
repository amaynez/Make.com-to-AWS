import os
import boto3
from botocore.exceptions import ClientError
from PIL import Image
from huggingface_hub import InferenceClient
import io
import uuid

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

def lambda_handler(event, context):
    # Get the input content from the event
    flux_prompt = event.get("FluxPromptOut", {})
    flux_prompt = flux_prompt.get('body', '')
    flux_prompt = flux_prompt.strip()

    secret_name = os.environ['SECRET']
    region_name = os.environ['REGION']
    bucket_name = os.environ['S3_BUCKET_NAME'] 
    secret_string = get_secret(secret_name, region_name)

    try:
        client = InferenceClient(model="black-forest-labs/FLUX.1-dev", token=secret_string)

        image = client.text_to_image(flux_prompt)

        # Create a byte buffer to store the image data
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        # Generate a unique filename
        filename = f"flux_image_{uuid.uuid4()}.png"

        # Upload the image to S3
        s3_client = boto3.client('s3')
        s3_client.upload_fileobj(buffer, bucket_name, filename)

        # Generate the S3 URL
        s3_url = f"https://{bucket_name}.s3.amazonaws.com/{filename}"

        return {
            'statusCode': 200,
            'body': s3_url
        }
    except Exception as e:
        print(f"Caught unexpected error: {str(e)}")
        raise e