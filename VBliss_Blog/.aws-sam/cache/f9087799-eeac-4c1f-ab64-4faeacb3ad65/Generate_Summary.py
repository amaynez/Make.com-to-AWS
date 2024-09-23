import json
import os
import boto3

"""
This Lambda function generates a summary for a blog post using Amazon Bedrock AI models.
It takes blog post metadata and content as input, prepares a prompt for the AI model,
and attempts to generate a summary using multiple Bedrock models in case of failures.

Key features:
- Extracts blog post title, keywords, and content from the input event
- Uses environment variables for system and user prompts
- Tries multiple Bedrock AI models in case of failures
- Returns the generated summary along with the successful model ID
"""

def lambda_handler(event, context):
    # Extract data from event
    payload = event.get("Payload", {})
    meta_response = payload.get("metaOut", {})
    blog_post = payload.get("blogPost", {})
    
    # Parse JSON responses from previous steps
    meta_content = json.loads(meta_response.get('body', '{}'))
    post_content = json.loads(blog_post.get('body', '{}'))

    # Prepare prompt components
    title = meta_content.get('title', '')
    keywords = meta_content.get('keywords', '')
    blog_body = post_content.get('blog_post', '').strip()

    # Retrieve prompts from environment variables and format them
    system_prompt = os.environ['SYSTEM_PROMPT']
    user_prompt = os.environ['USER_PROMPT'].replace("#####", title).replace("$$$$$", blog_body).replace("!!!!!", keywords)

    # Prepare request body for Bedrock API
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 32000,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": f"{system_prompt}\n\n{user_prompt}"}]
            }
        ]
    }

    # Create Bedrock client and get model IDs from environment variables
    bedrock_runtime = boto3.client('bedrock-runtime')
    model_ids = [os.environ[f'BEDROCK_MODEL_ID_{i}'] for i in range(1, 5)]

    # Try each model in sequence until successful or all fail
    for model_id in model_ids:
        try:
            # Invoke Bedrock model
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            # Parse response and extract generated text
            response_data = json.loads(response['body'].read())
            response_text = response_data['content'][0]['text']

            # Return successful response with generated summary and model ID
            return {
                'statusCode': 200,
                'body': json.dumps({'summary': response_text}),
                'headers': {
                    'Content-Type': 'application/json',
                    'modelUsed': model_id
                }
            }
        except Exception as e:
            # Log error and continue to next model
            print(f"Error with model {model_id}: {str(e)}")

    # If all models fail, raise an exception
    raise Exception("All models failed to generate output.")