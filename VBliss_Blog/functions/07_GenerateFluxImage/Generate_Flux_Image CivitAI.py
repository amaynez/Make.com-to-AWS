import os
import boto3
from botocore.exceptions import ClientError
import io
import uuid
import logging
import traceback
import civitai
from PIL import Image
from IPython.display import Image

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
    prompt = event.get("FluxPromptOut", {}).get('body', '').strip()
    region_name = os.environ['REGION']
    bucket_name = os.environ['S3_BUCKET_NAME']
    model_urn = os.environ['MODEL_URN']
    token = get_secret(os.environ['SECRET'], region_name)
    
    os.environ['CIVITAI_API_TOKEN'] = token
 
    s3_url = ""

    input = {
        "model": model_urn,
        "params": {
            "prompt": prompt,
            "negativePrompt": "(deformed iris, deformed pupils, semi-realistic, cgi, 3d, render, sketch, cartoon, drawing, anime, mutated hands and fingers:1.4), (deformed, distorted, disfigured:1.3)",
            "scheduler": "EulerA",
            "steps": 20,
            "cfgScale": 7,
            "width": 1024,
            "height": 640,
            "clipSkip": 2
        }
    }

    try:
        response = civitai.image.create(input, wait=True)
        
        logger.info(f"API Response: {response}")

        if response['jobs'][0]['result'].get('available'):
            image_url = response['jobs'][0]['result'].get('blobUrl')
            if image_url:
                image_bytes=Image(url=image_url)
            else:
                logger.error("Image URL not found in the job result.")
                print("Image URL not found in the job result.")
                raise Exception("Image URL not found in the job result.")
                
        else:
            logger.error("No image was created, the job is not yet complete, or the result is not available.")
            print("No image was created, the job is not yet complete, or the result is not available.")
            raise Exception("No image was created, the job is not yet complete, or the result is not available.")

        s3_url = upload_image_to_s3(image_bytes, bucket_name, region_name)
        
        return {
            'statusCode': 200,
            'body': s3_url
        }
    
    except Exception as e:
        logger.error(f"Failed to process request: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise e