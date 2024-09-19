import json
import requests
from requests.auth import HTTPBasicAuth
import boto3
from botocore.exceptions import ClientError
import os
from urllib.parse import urlparse
import logging

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

def get_image_from_s3(s3_url, region_name='us-west-2'):
    s3 = boto3.client('s3', region_name=region_name)
    parsed_url = urlparse(s3_url)
    bucket_name = parsed_url.netloc.split('.')[0]
    object_key = parsed_url.path.lstrip('/')

    print(f"Attempting to retrieve object from bucket: {bucket_name}, key: {object_key}")

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

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    #try:
    # Extract the data needed from the event body
    parsed_prompt_response = json.loads(json.dumps(event["FluxPromptOut"]))
    alt_text = json.loads(parsed_prompt_response.get('body', '{}'))

    print(f"Alt text: {alt_text}")

    try:
        parsed_image_response = event.get("FluxImage", {})
        s3_image_url = parsed_image_response.get("body", "")
        filename = s3_image_url.split('/')[-1] if s3_image_url else ""
    except Exception as e:
        print(f"Error processing image url: {str(e)}")

    region = os.environ['REGION']

    meta_content = json.loads(event["metaOut"]["body"])
    title = meta_content.get('title')

    print(f"Titulo: {title}")

    # Retrieve image from S3
    image_data = get_image_from_s3(s3_image_url,region)

    print(f"Image data: {image_data}")

    # WordPress API endpoint
    wp_api_url = os.environ['API_URL']
    
    print(f"Wordpress API URL: {wp_api_url}")

    # Retrieve Wordpress Credentials
    wp_secret_str = get_secret(os.environ['SECRET'], region)
    wp_secret = json.loads(wp_secret_str)
    wp_username = wp_secret.get('username')
    wp_password = wp_secret.get('password')

    # Prepare headers
    headers = {
        'Content-Disposition': f'attachment; filename={filename}',
        'Content-Type': 'image/png'
    }
    
    print(f"Headers: {headers}")

    payload = {
        'file': image_data,
        'title': title,
        'alt_text': alt_text,
        'caption': 'Imagen generada por Flux AI'
    }

    print(f"Payload: {payload}")

    # Make the API request
    response = requests.post(
        wp_api_url,
        headers=headers,
        auth=HTTPBasicAuth(wp_username, wp_password),
        data=payload
    )

    print(f"Wordpress response: {response}")
    print(f"Wordpress response text: {response.text}")
    print(f"Wordpress response status code: {response.status_code}")
    print(f"Wordpress response headers: {response.headers}")
    print(f"Wordpress response json: {response.json()}")
    print(f"Wordpress response url: {response.url}")

    if response.status_code == 201:
        result=response.json()
        return {
            'statusCode': 200,
            'body': json.dumps({
                'media_id': result['id'],
                'url': result['source_url']
                })
        }
    else:
        raise Exception(f"Failed to upload image: {response.text}")   
    #except Exception as e:
    #    raise Exception(f"Error in Lambda function: {str(e)}")