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
    featured_image_id = json.loads(parsed_wpimage_response).get('media_id', '{}')

    blog_post = event.get("blogPost")
    body_content_post = json.loads(blog_post.get('body', '{}'))
    post_text = body_content_post.get('blog_post', '')

    parsed_meta_response = event["metaOut"]
    meta_content = json.loads(parsed_meta_response.get('body', '{}'))
    title = meta_content.get('title')
    category_id = meta_content.get('category_id')

    blog_summary = event.get("SummaryOut")
    body_summary_post = json.loads(blog_summary.get('body', '{}'))
    excerpt = body_summary_post.get('summary', '')
  
    # Retrieve Wordpress Credentials
    wp_secret_str = get_secret(os.environ['SECRET'], os.environ['REGION'])
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

    token = requests.post('https://public-api.wordpress.com/oauth2/token', data=data).json()['access_token']

    # WordPress API endpoint
    wp_api_url = os.environ['API_URL']
    wp_api_url = wp_api_url.replace("$site", str(site_id))

    # Prepare headers
    headers = {
        'authorization': f'Bearer {token}'
    }
    
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
        headers=headers,
        json=post_data
    )
    
    if response.status_code == 200:
        return {
            'statusCode': 200,
            'body': response.json()['URL']
        }
    else:
        raise Exception(response.text)