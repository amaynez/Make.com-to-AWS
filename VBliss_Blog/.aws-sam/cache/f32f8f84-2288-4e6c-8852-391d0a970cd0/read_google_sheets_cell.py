import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name, region_name):

    # Create a Secrets Manager client
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
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    return get_secret_value_response

def lambda_handler(event, context):
    secret_name = os.environ['SECRET_NAME']
    region_name = os.environ['REGION_NAME']
    secret = json.loads(get_secret(secret_name, region_name))

    # Create credentials using the JSON data from Secrets Manager
    credentials = service_account.Credentials.from_service_account_info(secret)

    # Create a Google Sheets API client
    sheets_service = build('sheets', 'v4', credentials=credentials)
    
    # Set the ID of the Google Sheets spreadsheet and the range to read
    spreadsheet_id = os.environ['SPREADSHEET_ID']
    range_name = os.environ['RANGE_NAME']
    
    # Read the values from the specified range
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        print('No data found.')
        return None
    
    # Find the first empty value in column A
    for i, row in enumerate(values):
        if row[0] == '':
                result = {
                     "title": row[1],
                     "keywords": row[7],
                     "category_id": row[9]
                }
                response = {
                    'statusCode': 200,
                    'body': json.dumps(result),
                    'headers': {
                        'Content-Type': 'application/json'
                    }
                }
                return response
    
    response = {
        'statusCode': 500,
        'body': json.dumps({'error': 'No empty cell found in column A'})
    }
    
    return response
