import json
import os
import boto3
from typing import Dict, Any

"""
This Lambda function is part of the VBliss_Blog system and is responsible for processing
individual sections of a blog post. It uses Amazon Bedrock to generate content for each
section based on the table of contents (TOC) item and metadata from previous steps.

Key features:
1. Retrieves system and user prompts from environment variables
2. Dynamically selects from multiple Bedrock models
3. Handles errors and retries with different models
4. Returns generated blog section content

The function is designed to be flexible and fault-tolerant, attempting to use multiple
models if the primary one fails.
"""

# Helper function to safely retrieve environment variables
def get_env_variable(key: str, default: str = '') -> str:
    """
    Safely retrieve an environment variable, returning a default value if not found.
    """
    return os.environ.get(key, default)

# Function to create the request body for the Bedrock model
def create_request_body(system_prompt: str, user_prompt: str) -> Dict[str, Any]:
    """
    Create a properly formatted request body for the Bedrock model API.
    """
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 32000,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"{system_prompt}\n\n{user_prompt}"
                    }
                ]
            }
        ]
    }

# Function to invoke the Bedrock model and return the response
def invoke_bedrock_model(bedrock_runtime, model_id: str, request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Invoke the specified Bedrock model with the given request body and return the response.
    """
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        contentType='application/json',
        accept='application/json',
        body=json.dumps(request_body)
    )
    return json.loads(response['body'].read())

# Main Lambda handler function
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda function handler. Processes a single blog section using Bedrock models.
    """
    # Extract relevant information from the event
    toc_item = event["item"]
    meta_response = event["metaOut"]
    
    # Parse metadata from the previous step
    body_content_meta = json.loads(meta_response.get('body', '{}'))
    title = body_content_meta.get('title', '')
    keywords = body_content_meta.get('keywords', '')
    
    # Prepare prompts using environment variables and extracted data
    system_prompt = get_env_variable('SYSTEM_PROMPT').replace("#####", title)
    user_prompt = get_env_variable('USER_PROMPT').replace("#####", toc_item).replace("$$$$$", keywords)

    # Initialize Bedrock runtime client
    bedrock_runtime = boto3.client('bedrock-runtime')
    
    # Get model IDs from environment variables
    model_ids = [get_env_variable(f'BEDROCK_MODEL_ID_{i}') for i in range(1, 5)]
    
    # Create the request body
    request_body = create_request_body(system_prompt, user_prompt)

    # Try each model in sequence until successful or all fail
    for model_id in model_ids:
        try:
            # Invoke the Bedrock model
            response_data = invoke_bedrock_model(bedrock_runtime, model_id, request_body)
            response_text = response_data['content'][0]['text']

            # Return successful response
            return {
                'statusCode': 200,
                'body': json.dumps({'blog_section': response_text}),
                'headers': {'Content-Type': 'application/json'}
            }
        except json.JSONDecodeError as json_err:
            # Log JSON decoding errors
            print(f"JSON decoding error with model {model_id}: {str(json_err)}\nResponse text: {response_text}")
        except Exception as e:
            # Log any other errors
            print(f"An error occurred with model {model_id}: {str(e)}")

    # If all models fail, raise an exception
    raise Exception("All models failed to generate output.")