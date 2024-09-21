import os
import json
from datetime import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
from botocore.exceptions import ClientError

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

    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']
    else:
        return get_secret_value_response['SecretBinary']

def parse_json_body(event, key):
    response = json.loads(json.dumps(event.get(key, {})))
    return json.loads(response.get('body', '{}'))

def get_nested_value(data, *keys, default=''):
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, {})
        else:
            return default
    return data if data != {} else default

def lambda_handler(event, context):
    # Get environment variables
    secret_name = os.environ['SECRET']
    region_name = os.environ['REGION']
    spreadsheet_id = os.environ['SPREADSHEET_ID']

    # Get the secret
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

    # Extract specific values
    title = get_nested_value(parsed_meta_content, 'title')
    row_number = get_nested_value(parsed_meta_content, 'row_number')
    excerpt = get_nested_value(parsed_summary, 'summary')
    image_url = get_nested_value(parsed_wpimage_response, 'url')
    post_url = get_nested_value(parsed_image_response, 'body')
    flux_prompt = get_nested_value(parsed_flux_prompt, 'body')

    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Prepare the values to update
    values = [
        [post_url, title, title, image_url, flux_prompt, excerpt, current_datetime]
    ]

    # Prepare the range to update (assuming the spreadsheet starts from A1)
    range_name = f'A{row_number}:G{row_number}'

    # Update the cells
    request = sheets_service.spreadsheets().values().update(
    spreadsheetId=spreadsheet_id,
    range=range_name,
    valueInputOption='RAW',
    body={'values': values}
    )

    try:
        response = request.execute()

        result = {
            'updatedCells': response.get('updatedCells'),
            'updatedRange': response.get('updatedRange')
        }

        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
