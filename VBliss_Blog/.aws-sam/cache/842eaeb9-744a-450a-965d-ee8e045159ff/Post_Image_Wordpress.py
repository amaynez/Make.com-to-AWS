"""
This script is an AWS Lambda function that handles the process of uploading an image to WordPress.
It performs the following main tasks:
1. Retrieves an image from an S3 bucket
2. Fetches WordPress credentials from AWS Secrets Manager
3. Authenticates with WordPress and obtains an access token
4. Uploads the image to WordPress with associated metadata
5. Returns the media ID and URL of the uploaded image

The script is designed to work within an AWS environment and requires specific environment variables
and event structure.
"""

import json
import requests
import boto3
from botocore.exceptions import ClientError
import os
from urllib.parse import urlparse
import logging

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

def get_image_from_s3(s3_url, region_name='us-west-2'):
    """
    Retrieve an image from an S3 bucket.
    
    :param s3_url: S3 URL of the image
    :param region_name: AWS region where the S3 bucket is located
    :return: Image content as bytes
    """
    s3 = boto3.client('s3', region_name=region_name)
    parsed_url = urlparse(s3_url)
    bucket_name = parsed_url.netloc.split('.')[0]
    object_key = parsed_url.path.lstrip('/')

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
    """
    Main Lambda function handler.
    
    :param event: Lambda event containing input data
    :param context: Lambda context
    :return: Dictionary with status code and uploaded image details
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    try:
        # Extract data from event
        parsed_prompt_response = event["FluxPromptOut"]
        alt_text = json.loads(parsed_prompt_response.get('body', '{}'))
        
        parsed_image_response = event.get("FluxImage", {})
        s3_image_url = parsed_image_response.get("body", "")
        filename = s3_image_url.split('/')[-1] if s3_image_url else ""

        meta_content = json.loads(event["metaOut"]["body"])
        title = meta_content.get('title')

        region = os.environ['REGION']

        # Retrieve image from S3
        image_data = get_image_from_s3(s3_image_url, region)

        # Retrieve WordPress Credentials
        wp_secret = json.loads(get_secret(os.environ['SECRET'], region))
        
        # Authenticate and get access token
        token = get_wordpress_token(wp_secret)

        # Upload image to WordPress
        media_id, media_url = upload_image_to_wordpress(token, wp_secret['site_id'], filename, image_data, title, alt_text)

        return {
            'statusCode': 200,
            'body': json.dumps({
                'media_id': media_id,
                'url': media_url
            })
        }
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        raise

def get_wordpress_token(wp_secret):
    data = {
        'grant_type': 'password',
        'username': wp_secret['username'],
        'password': wp_secret['password'],
        'client_id': wp_secret['client_id'],
        'client_secret': wp_secret['client_secret'],
        'redirect_uri': wp_secret['redirect_uri'],
        'blog_id': wp_secret['site_id']
    }

    response = requests.post('https://public-api.wordpress.com/oauth2/token', data=data)
    response.raise_for_status()
    return response.json()['access_token']

def upload_image_to_wordpress(token, site_id, filename, image_data, title, alt_text):
    wp_api_url = os.environ['API_URL'].replace("$site", str(site_id))
    
    headers = {'authorization': f'Bearer {token}'}
    
    files = {'media[0]': (filename, image_data, 'image/png')}
    
    data = {
        'attrs[0]': json.dumps({
            'caption': 'Imagen generada por Flux AI',
            'title': title,
            'alt_text': alt_text,
            'description': alt_text,
            'status': 'publish',
            'filename': filename
        })
    }

    response = requests.post(wp_api_url, headers=headers, files=files, data=data)
    response.raise_for_status()
    result = response.json()
    media_item = result['media'][0]
    return media_item['ID'], media_item['URL']