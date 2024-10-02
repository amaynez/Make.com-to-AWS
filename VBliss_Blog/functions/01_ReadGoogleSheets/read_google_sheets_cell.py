"""
This script is a Lambda function that interacts with Google Sheets API to find the next available blog post to create.

Key features:
1. Retrieves Google Sheets API credentials from AWS Secrets Manager
2. Connects to a specified Google Sheet
3. Finds the first empty cell in column A with non-empty data in column B
4. Returns relevant information for the next blog post to be created

The script is designed to be run as an AWS Lambda function and requires specific environment variables to be set.
"""

import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
import boto3
from botocore.exceptions import ClientError

# Function to retrieve a parameter from AWS Systems Manager Parameter Store
def get_parameter(parameter_name, region_name):
    """
    Retrieve a parameter from AWS Systems Manager Parameter Store.

    Args:
        parameter_name (str): The name of the parameter to retrieve.
        region_name (str): The AWS region where the parameter is stored.

    Returns:
        str: The parameter value.

    Raises:
        ClientError: If there's an error retrieving the parameter.
    """
    ssm = boto3.client('ssm', region_name=region_name)

    try:
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        # If there's an error, re-raise it
        raise e

# Function to create and return a Google Sheets service object
def get_sheets_service(parameter_name, region_name):
    """
    Create and return a Google Sheets service object.

    Args:
        parameter_name (str): The name of the parameter containing Google Sheets API credentials.
        region_name (str): The AWS region where the parameter is stored.

    Returns:
        googleapiclient.discovery.Resource: A Google Sheets service object.
    """
    # Get the parameter containing Google Sheets API credentials
    credentials_json = get_parameter(parameter_name, region_name)
    credentials_dict = json.loads(credentials_json)
    # Create credentials from the parameter
    credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    # Build and return the Google Sheets service object
    return build('sheets', 'v4', credentials=credentials)

# Function to find the first empty cell in column A and return relevant information
def find_first_empty_cell(values):
    """
    Find the first empty cell in column A with non-empty data in column B.

    Args:
        values (list): A 2D list containing the values from the Google Sheet.

    Returns:
        dict: A dictionary containing relevant information for the next blog post.

    Raises:
        Exception: If no pending blog post is found or if no empty cell is found in column A with a non-empty cell in column B.
    """
    for i, row in enumerate(values):
        if not row[0]:  # If the first column (A) is empty
            if not row[1]:  # If the second column (B) is also empty
                raise Exception('No pending blog post to create')
            # Return a dictionary with relevant information
            return {
                "title": row[1],        # Column B: Title
                "keywords": row[7],     # Column H: Keywords
                "category_id": row[9],  # Column J: Category ID
                "row_number": i + 1     # Row number (1-indexed)
            }
    # If no empty cell is found in column A with a non-empty cell in column B
    raise Exception('No empty cell found in column A with a non-empty cell in column B')

# Main Lambda function handler
def lambda_handler(event, context):
    """
    Main Lambda function handler.

    This function retrieves data from a Google Sheet, finds the next available blog post,
    and returns the relevant information.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.

    Returns:
        dict: A dictionary containing the status code, body (with blog post information),
              and headers for the HTTP response.

    Raises:
        Exception: If no data is found in the Google Sheet.
    """
    # Retrieve environment variables
    parameter_name = os.environ['PARAMETER_NAME']
    region_name = os.environ['REGION_NAME']
    spreadsheet_id = os.environ['SPREADSHEET_ID']
    range_name = os.environ['RANGE_NAME']

    # Get the Google Sheets service object
    sheets_service = get_sheets_service(parameter_name, region_name)
    
    # Retrieve values from the specified range in the spreadsheet
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name
    ).execute()
    
    values = result.get('values', [])
    
    if not values:
        raise Exception('No data found')
    
    # Find the first empty cell and get relevant information
    result = find_first_empty_cell(values)
    
    # Return the result as a JSON response
    return {
        'statusCode': 200,
        'body': json.dumps(result),
        'headers': {
            'Content-Type': 'application/json'
        }
    }
