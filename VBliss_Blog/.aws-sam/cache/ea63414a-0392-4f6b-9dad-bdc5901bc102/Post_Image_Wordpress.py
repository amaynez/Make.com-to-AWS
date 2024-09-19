import json
import base64
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

def get_image_from_s3(s3_url):
    s3 = boto3.client('s3')
    parsed_url = urlparse(s3_url)
    bucket_name = parsed_url.netloc
    object_key = parsed_url.path.lstrip('/')

    try:
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        image_content = response['Body'].read()
        return image_content
    except ClientError as e:
        raise Exception(f"Error retrieving image from S3: {str(e)}")

def lambda_handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    try:
        # Extract the data needed from the event body
        parsed_prompt_response = json.loads(json.dumps(event["FluxPromptOut"]))
        alt_text = json.loads(parsed_prompt_response.get('body', '{}'))

        print(f"Alt text: {alt_text}")

        parsed_image_response = json.loads(json.dumps(event["FluxImage"]))
        s3_image_url = json.loads(parsed_image_response.get('body', '{}'))
        filename = s3_image_url.split('/')[-1]

        print(f"Filename: {filename}")
        print(f"Image URL: {s3_image_url}")

        # Retrieve image from S3
        image_data = get_image_from_s3(s3_image_url)

        print(f"Image data: {image_data}")

        parsed_meta_response = json.loads(json.dumps(event["metaOut"]))  
        meta_content = json.loads(parsed_meta_response.get('body', '{}'))
        title = meta_content.get('title')

        print(f"Title: {title}")

        # Convert binary to base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        
        print(f"Image data base64: {base64_data}")

        # WordPress API endpoint
        wp_api_url = os.environ['API_URL']
        
        # WordPress credentials
        wp_secret = get_secret(os.environ['SECRET'], os.environ['REGION'])
        wp_username = wp_secret.get('username')
        wp_password = wp_secret.get('password')
        
        # Prepare headers
        headers = {
            'Content-Disposition': f'attachment; filename={filename}',
            'Content-Type': 'image/png'
        }
        
        payload = {
            'file': base64_data,
            'title': title,
            'alt_text': alt_text,
            'caption': 'Imagen generada por Flux AI'
        }

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
    except Exception as e:
        raise Exception(f"Error in Lambda function: {str(e)}")