import json
import requests
from requests.auth import HTTPBasicAuth
import boto3
from botocore.exceptions import ClientError
import os

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
    # Extract the data needed from the event body
    parsed_wpimage_response = event.get("WordpressImage", {}).get("body")
    featured_image_id = json.loads(parsed_wpimage_response['media_id', '{}'])

    parsed_image_response = json.loads(json.dumps(event["blogPost"]))
    post_text = json.loads(parsed_image_response['body', '{}'])

    parsed_meta_response = json.loads(json.dumps(event["metaOut"]))  
    meta_content = json.loads(parsed_meta_response.get('body', '{}'))
    title = meta_content.get('title')
    category_id = meta_content.get('category_id')

    parsed_image_response = json.loads(json.dumps(event["SummaryOut"]))
    excerpt = json.loads(parsed_image_response['body', '{}'])
    
    # WordPress API endpoint
    wp_api_url = os.environ['API_URL']
    
    # WordPress credentials
    wp_secret = get_secret(os.environ['SECRET'], os.environ['REGION'])
    wp_username = wp_secret.get('username')
    wp_password = wp_secret.get('password')
    
    # Prepare the post data
    post_data = {
        'title': title,
        'content': post_text,
        'excerpt': excerpt,
        'featured_image': featured_image_id,
        'categories': [category_id],
        'status': 'publish'
    }
    
    # Make the API request
    response = requests.post(
        wp_api_url,
        auth=HTTPBasicAuth(wp_username, wp_password),
        json=post_data
    )
    
    if response.status_code == 201:
        return {
            'statusCode': 200,
            'body': response.json()['URL']
        }
    else:
        return {
            'statusCode': 400,
            'body': json.dumps({'message': 'Failed to create post', 'error': response.text})
        }