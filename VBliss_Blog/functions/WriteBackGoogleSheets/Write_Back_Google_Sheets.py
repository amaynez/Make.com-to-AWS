"""
This script is a Lambda function that updates a Google Sheets spreadsheet with blog post information.
Its purpose is to write the results of the blog post creation process to a Google Sheet so that the next iteration
of the automation knows which posts it has already created and which it needs to create.

It performs the following main tasks:
1. Retrieves secret credentials from AWS Secrets Manager
2. Authenticates with Google Sheets API
3. Extracts blog post data from the Lambda event
4. Updates a specific row in the Google Sheets spreadsheet with the blog post information
5. Returns the result of the update operation

The script is designed to work within an AWS Lambda environment and expects certain environment
variables and event structure to be present.
"""

import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name):
    """
    Retrieve a secret from AWS Secrets Manager.
    
    :param secret_name: Name of the secret in Secrets Manager
    :param region_name: AWS region where the secret is stored
    :return: Secret string or binary data
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

def parse_json_body(event, key):
    """
    Parse JSON body from the Lambda event for a specific key.
    
    :param event: Lambda event dictionary
    :param key: Key to extract from the event
    :return: Parsed JSON object
    """
    response = json.loads(json.dumps(event.get(key, {})))
    return json.loads(response.get('body', '{}'))

def get_nested_value(data, *keys, default=''):
    """
    Safely get a nested value from a dictionary.
    
    :param data: Dictionary to search
    :param keys: Sequence of keys to traverse
    :param default: Default value if key is not found
    :return: Value found at the nested location or default
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return default
    return data if data != {} else default

def lambda_handler(event, context):
    """
    Main Lambda function handler.
    
    :param event: Lambda event containing blog post information
    :param context: Lambda context
    :return: Dictionary with status code, body, and headers
    """
    # Get environment variables
    secret_name = os.environ['SECRET']
    region_name = os.environ['REGION']
    spreadsheet_id = os.environ['SPREADSHEET_ID']

    # Get the secret from AWS Secrets Manager
    secret_string = get_secret(secret_name, region_name)
    secret = json.loads(secret_string)

    # Create credentials using the JSON data from Secrets Manager
    credentials = service_account.Credentials.from_service_account_info(secret)

    # Create a Google Sheets API client
    sheets_service = build('sheets', 'v4', credentials=credentials)

    # Extract data from event
    parsed_meta_content = parse_json_body(event, "metaOut")
    parsed_summary = parse_json_body(event, "SummaryOut")
    parsed_wpimage_response = parse_json_body(event, "WordpressImage")
    parsed_flux_prompt = json.loads(json.dumps(event.get("FluxPromptOut", {})))
    parsed_image_response = json.loads(json.dumps(event.get("WordpressPostURL", {})))

    # Extract specific values from parsed data
    title = get_nested_value(parsed_meta_content, 'title')
    row_number = get_nested_value(parsed_meta_content, 'row_number')
    excerpt = get_nested_value(parsed_summary, 'summary')
    image_url = get_nested_value(parsed_wpimage_response, 'url')
    post_url = get_nested_value(parsed_image_response, 'body')
    flux_prompt = get_nested_value(parsed_flux_prompt, 'body')

    # Get current datetime for timestamp
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare the values to update in the spreadsheet
    values = [
        [post_url, title, title, image_url, flux_prompt, excerpt, current_datetime]
    ]

    # Prepare the range to update (assuming the spreadsheet starts from A1)
    range_name = f'A{row_number}:G{row_number}'

    # Update the cells in the Google Sheets spreadsheet
    request = sheets_service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption='RAW',
        body={'values': values}
    )

    try:
        # Execute the update request
        response = request.execute()

        # Prepare the result dictionary
        result = {
            'updatedCells': response.get('updatedCells'),
            'updatedRange': response.get('updatedRange')
        }

        # Return successful response
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    except Exception as e:
        # If an error occurs during the update, raise an exception
        raise Exception(f"Error updating Google Sheets: {e}")

