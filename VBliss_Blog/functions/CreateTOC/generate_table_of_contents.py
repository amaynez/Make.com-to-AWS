"""
This script is a Lambda function that generates a table of contents (TOC) for a given title.
It uses Amazon Bedrock to invoke AI models for content generation.

The main steps are:
1. Extract the title from the input event
2. Construct a user prompt with the title
3. Invoke Bedrock models to generate a JSON response containing TOC data
4. Parse and aggregate the TOC items into top level items which include sub-items to facilitate LLM generation
5. Return the formatted TOC as a string

The script includes error handling and will attempt to use multiple models if earlier ones fail.
"""

import json
import os
import boto3

def aggregate_tdc_items(tdc):
    #Recursively aggregate TOC items into a formatted string.
    def recursive_aggregate(item, prefix=""):
        content = [prefix + item['titulo']]
        content.extend(recursive_aggregate(subtema, prefix + "  ") for subtema in item.get('sub-temas', []))
        return '\n'.join(content)

    return [recursive_aggregate(top_level_item) for top_level_item in tdc]

def extract_first_json(text):
    #Extract the first valid JSON object from a string.
    stack, start = [], -1
    for i, char in enumerate(text):
        if char == '{':
            if not stack: start = i
            stack.append(char)
        elif char == '}' and stack:
            stack.pop()
            if not stack: return text[start:i+1]
    return None

def lambda_handler(event, context):
    # Extract the parsed response from the event
    parsed_response = event["metaOut"]
    if parsed_response['statusCode'] != 200:
        raise Exception(f"Error: {parsed_response}")
    
    # Extract the title and construct the user prompt
    title = json.loads(parsed_response['body'])['title']
    user_prompt = os.environ['USER_PROMPT'].replace("#####", title)

    # Initialize Bedrock client
    bedrock_runtime = boto3.client('bedrock-runtime')
    
    # Prepare the request body for Bedrock
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 32000,
        "messages": [{"role": "user", "content": [{"type": "text", "text": f"{os.environ['SYSTEM_PROMPT']}\n\n{user_prompt}"}]}]
    }

    # Try different Bedrock models in case of failures
    for model_id in [os.environ[f'BEDROCK_MODEL_ID_{i}'] for i in range(1, 5)]:
        try:
            # Invoke the Bedrock model
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            response_text = json.loads(response['body'].read())['content'][0]['text']
            json_text = extract_first_json(response_text)
            if not json_text:
                raise ValueError("No JSON content found")

            result = aggregate_tdc_items(json.loads(json_text)["tdc"])
            return {'statusCode': 200, 'body': result, 'headers': {'Content-Type': 'application/json', 'model used': model_id}}
        
        except Exception as e:
            print(f"Error with model {model_id}: {str(e)}")

    raise Exception("All models failed to generate output.")
