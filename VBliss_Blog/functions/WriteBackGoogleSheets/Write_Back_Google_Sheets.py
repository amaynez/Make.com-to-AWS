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

    # Extract the data needed from the event body
    parsed_meta_response = json.loads(json.dumps(event["metaOut"]))  
    meta_content = json.loads(parsed_meta_response.get('body', '{}'))
    title = meta_content.get('title')
    row_number = meta_content.get('row_number')

    parsed_image_response = json.loads(json.dumps(event["SummaryOut"]))
    excerpt = json.loads(parsed_image_response['body', '{}'])

    parsed_wpimage_response = event.get("WordpressImage", {}).get("body")
    image_url = json.loads(parsed_wpimage_response['url', '{}'])

    parsed_image_response = json.loads(json.dumps(event["FluxPromptOut"]))
    flux_prompt = json.loads(parsed_image_response['body', '{}'])

    parsed_image_response = json.loads(json.dumps(event["WordpressPostURL"]))
    post_url = json.loads(parsed_image_response['body', '{}'])

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
