"""
This script is a Lambda function that posts a blog article to WordPress.com using their REST API.

It performs the following main tasks:
1. Retrieves secret credentials from AWS Secrets Manager
2. Extracts blog post data from the Lambda event
3. Obtains an OAuth access token from WordPress.com
4. Posts the blog article to WordPress.com using the REST API

The script expects the following environment variables:
- SECRET: Name of the secret in AWS Secrets Manager
- REGION: AWS region where the secret is stored
- API_URL: WordPress.com API URL template

The Lambda event should contain the following data:
- WordpressImage: Featured image information
- blogPost: Main content of the blog post
- metaOut: Metadata including title and category
- SummaryOut: Blog post excerpt/summary
"""

import json
import os
from functools import lru_cache
import boto3
import requests
from botocore.exceptions import ClientError

@lru_cache(maxsize=1)
def get_secret(secret_name, region_name):
    """
    Retrieve a secret from AWS Secrets Manager.
    
    :param secret_name: Name of the secret in Secrets Manager
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
        # If there's an error, re-raise it
        raise e

    # Return the secret string directly
    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']
    else:
        # In case the secret is binary
        return get_secret_value_response['SecretBinary']

def lambda_handler(event, context):
    """
    Main Lambda function handler.
    
    :param event: Lambda event containing blog post data
    :param context: Lambda context
    :return: Dictionary with statusCode and the URL of the published post
    """
    # Extract data from event
    wp_image_data = json.loads(event.get("WordpressImage", {}).get("body", "{}"))
    featured_image_id = wp_image_data.get('media_id')

    blog_post_data = json.loads(event.get("blogPost", {}).get('body', '{}'))
    post_text = blog_post_data.get('blog_post', '')

    meta_content = json.loads(event.get("metaOut", {}).get('body', '{}'))
    title = meta_content.get('title')
    category_id = meta_content.get('category_id')

    summary_data = json.loads(event.get("SummaryOut", {}).get('body', '{}'))
    excerpt = summary_data.get('summary', '')
  
    # Retrieve WordPress Credentials from Secrets Manager
    wp_secret = json.loads(get_secret(os.environ['SECRET'], os.environ['REGION']))
    
    # Prepare OAuth data for token request
    oauth_data = {
        'grant_type': 'password',
        'username': wp_secret['username'],
        'password': wp_secret['password'],
        'client_id': wp_secret['client_id'],
        'client_secret': wp_secret['client_secret'],
        'redirect_uri': wp_secret['redirect_uri'],
        'blog_id': wp_secret['site_id']
    }

    # Get access token from WordPress.com
    token_response = requests.post('https://public-api.wordpress.com/oauth2/token', data=oauth_data)
    token_response.raise_for_status()
    token = token_response.json()['access_token']

    # Prepare WordPress API request
    wp_api_url = os.environ['API_URL'].replace("$site", str(wp_secret['site_id']))
    headers = {'Authorization': f'Bearer {token}'}
    post_data = {
        'title': title,
        'content': post_text,
        'excerpt': excerpt,
        'featured_image': featured_image_id,
        'categories': [category_id],
        'status': 'publish'
    }
    
    # Make the API request to create the post
    response = requests.post(wp_api_url, headers=headers, json=post_data)
    response.raise_for_status()
    
    # Return the URL of the published post
    return {
        'statusCode': 200,
        'body': response.json()['URL']
    }