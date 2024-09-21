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

    # Extract the data needed from the event body
    parsed_prompt_response = json.loads(json.dumps(event["FluxPromptOut"]))
    alt_text = json.loads(parsed_prompt_response.get('body', '{}'))

    try:
        parsed_image_response = event.get("FluxImage", {})
        s3_image_url = parsed_image_response.get("body", "")
        filename = s3_image_url.split('/')[-1] if s3_image_url else ""
    except Exception as e:
        print(f"Error processing image url: {str(e)}")
        raise e

    region = os.environ['REGION']

    meta_content = json.loads(event["metaOut"]["body"])
    title = meta_content.get('title')

    # Retrieve image from S3
    image_data = get_image_from_s3(s3_image_url,region)

    # Retrieve Wordpress Credentials
    wp_secret_str = get_secret(os.environ['SECRET'], region)
    wp_secret = json.loads(wp_secret_str)
    client_secret = wp_secret.get('client_secret')
    client_id = wp_secret.get('client_id')
    redirect_uri = wp_secret.get('redirect_uri')
    site_id = wp_secret.get('site_id')
    username = wp_secret.get('username')
    password = wp_secret.get('password')

    data = {
        'grant_type': 'password',
        'username': username,
        'password': password,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'blog_id': site_id
    }

    response = requests.post('https://public-api.wordpress.com/oauth2/token', data=data)

    if response.status_code == 200:
        response_json = response.json()
        if 'access_token' in response_json:
            token = response_json['access_token']
        else:
            print(f"'access_token' not found in response. Keys present: {response_json.keys()}")
            raise KeyError("'access_token' not found in API response")
    else:
        print(f"Error response from API: {response.text}")
        raise Exception(f"API request failed with status code {response.status_code}, response: {response.text}")


    # WordPress API endpoint
    wp_api_url = os.environ['API_URL']
    wp_api_url = wp_api_url.replace("$site", str(site_id))

    # Prepare headers
    headers = {
        'authorization': f'Bearer {token}'
    }

    files = {
        'media[0]': (filename, image_data, 'image/png')
    }

    data = {
        'attrs[0]': {
            'caption': 'Imagen generada por Flux AI',
            'title': title,
            'alt_text': alt_text,
            'description': alt_text,
            'status': 'publish',
            'filename': filename
        }
    }


    # Make the API request
    response = requests.post(
        wp_api_url,
        headers=headers,
        files=files,  # Use files to send the image
        data=data  # Send metadata as form data
    )

    if response.status_code == 200:
        result=response.json()
        media_item = result['media'][0]
        media_id = media_item['ID']
        media_url = media_item['URL']
        return {
            'statusCode': 200,
            'body': json.dumps({
                'media_id': media_id,
                'url': media_url
                })
        }
    else:
        raise Exception(f"Failed to upload image: {response.text}")   