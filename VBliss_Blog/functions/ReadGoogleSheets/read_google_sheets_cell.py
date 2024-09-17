import os
from google.auth import default
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import json

def lambda_handler(event, context):
    # The credentials will be automatically obtained using Workload Identity Federation
    credentials, project = default()
    
    # If credentials require refreshing, do it now
    if credentials.expired:
        credentials.refresh(Request())

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
