"""
This script is a Lambda function that generates a prompt for a blog post using AWS Bedrock AI models.
It takes a blog summary and title as input, constructs a prompt using predefined templates,
and then attempts to generate content using multiple Bedrock models in a fallback sequence.

Key features:
- Extracts blog summary and title from the input event
- Constructs a prompt using environment variables and input data
- Attempts to generate content using multiple Bedrock AI models
- Returns the generated content along with the model used
- Implements error handling and fallback mechanisms
"""

import json
import os
import boto3

def get_event_data(event):
    #Extract blog summary and title from the input event.
    blog_summary = event.get("Payload", {}).get("SummaryOut", {})
    meta_response = event.get("Payload", {}).get("metaOut", {})
    
    summary = json.loads(blog_summary.get('body', '{}')).get('summary', '')
    title = json.loads(meta_response.get('body', '{}')).get('title', '')
    
    return summary, title

def create_request_body(system_prompt, user_prompt):
    #Create the request body for the Bedrock AI model invocation.
    return {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 32000,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": f"{system_prompt}\n\n{user_prompt}"}]
            }
        ]
    }

def invoke_bedrock_model(bedrock_runtime, model_id, request_body):
    #Invoke a Bedrock AI model and return the generated text and model ID.
    response = bedrock_runtime.invoke_model(
        modelId=model_id,
        contentType='application/json',
        accept='application/json',
        body=json.dumps(request_body)
    )
    response_data = json.loads(response['body'].read())
    return response_data['content'][0]['text'], model_id

def lambda_handler(event, context):
    # Extract blog summary and title from the event
    blog_summary, title = get_event_data(event)

    # Construct the prompt using environment variables and input data
    system_prompt = os.environ['SYSTEM_PROMPT']
    user_prompt = os.environ['USER_PROMPT'].replace("#####", title).replace("$$$$$", blog_summary)

    # Initialize Bedrock runtime client
    bedrock_runtime = boto3.client('bedrock-runtime')

    # Get model IDs to try in sequence from environment variables
    model_ids = [os.environ[f'BEDROCK_MODEL_ID_{i}'] for i in range(1, 5)]

    # Create the request body
    request_body = create_request_body(system_prompt, user_prompt)

    # Try each model in sequence until successful or all fail
    for model_id in model_ids:
        try:
            response_text, used_model = invoke_bedrock_model(bedrock_runtime, model_id, request_body)
            # Return successful response
            return {
                'statusCode': 200,
                'body': json.dumps(response_text),
                'headers': {
                    'Content-Type': 'application/json',
                    'Model-Used': used_model
                }
            }
        except Exception as e:
            print(f"An error occurred with model {model_id}: {str(e)}")

    # If all models fail, raise an exception
    raise Exception("All models failed to generate output.")
