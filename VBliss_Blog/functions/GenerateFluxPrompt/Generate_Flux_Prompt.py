import json
import os
import boto3

def lambda_handler(event, context):
    # Get the input content from the event
    blog_summary = event.get("Payload", {}).get("SummaryOut")
    meta_response = event.get("Payload", {}).get("metaOut")
 
    if meta_response is None or blog_summary is None:
        print("Error: 'metaOut' or 'blogSummary' not found in the event payload")
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'Missing expected section in event payload'})
        }

    body_content_meta = json.loads(meta_response.get('body', '{}'))
    title = body_content_meta.get('title')
    
    blog_body = blog_summary.get('body', '')
    blog_body = blog_body.strip()

    # Get the system prompt from the event (if provided)
    system_prompt = os.environ['SYSTEM_PROMPT']
    user_prompt = os.environ['USER_PROMPT'].replace("#####",title)
    user_prompt = user_prompt.replace("$$$$$", blog_body)

    # Create an Amazon Bedrock Runtime client
    bedrock_runtime = boto3.client('bedrock-runtime')
    
    # Define a list of model IDs to try
    model_ids = [
        os.environ['BEDROCK_MODEL_ID_1'],
        os.environ['BEDROCK_MODEL_ID_2'],
        os.environ['BEDROCK_MODEL_ID_3'],
        os.environ['BEDROCK_MODEL_ID_4']
    ]

    request_body = {
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

    for model_id in model_ids:
        try:
            # Make the API call to Amazon Bedrock using invoke_model
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            print(f"Model Used: {model_id}")

            # Parse the JSON response
            response_data = json.loads(response['body'].read())
            
            response_text = response_data['content'][0]['text']

            # Log the response text for debugging
            print(f"LLM Out: {response_text}")

            return {
                'statusCode': 200,
                'body': json.dumps(response_text),
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        except json.JSONDecodeError as json_err:
            error_message = f"JSON decoding error: {str(json_err)}\nResponse text: {response_text}"
            print(error_message)
        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            print(error_message)  # This will log the error in CloudWatch

    # If none of the models succeeded, return an error
    return {
        'statusCode': 500,
        'body': json.dumps({'error': 'All models failed to generate output.'})
    }