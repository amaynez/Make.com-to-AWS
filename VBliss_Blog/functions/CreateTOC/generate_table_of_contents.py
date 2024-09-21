import json
import os
import boto3

def aggregate_tdc_items(tdc):
    result = []

    def recursive_aggregate(item, prefix=""):
        content = prefix + item['titulo']
        if 'sub-temas' in item:
            for subtema in item['sub-temas']:
                content += "\n" + recursive_aggregate(subtema, prefix + "  ")
        return content

    for top_level_item in tdc:
        result.append(recursive_aggregate(top_level_item))
    
    return result

def extract_first_json(text):
    # Find the first occurrence of a JSON-like structure
    stack = []
    start = -1
    for i, char in enumerate(text):
        if char == '{':
            if not stack:
                start = i
            stack.append(char)
        elif char == '}':
            if stack:
                stack.pop()
                if not stack:
                    return text[start:i+1]
    return None

def lambda_handler(event, context):
    # Get the input content from the event
    parsed_response = json.loads(json.dumps(event["metaOut"]))
    status_code = parsed_response.get('statusCode')
    
    if status_code != 200:
        raise Exception(f"Error: {parsed_response}")
    
    body_content = json.loads(parsed_response.get('body', '{}'))
    title = body_content.get('title')
    
    # Get the system prompt from the event (if provided)
    system_prompt = os.environ['SYSTEM_PROMPT']
    user_prompt = os.environ['USER_PROMPT'].replace("#####",title)

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
        response_data = None
        try:
            # Make the API call to Amazon Bedrock using invoke_model
            response = bedrock_runtime.invoke_model(
                modelId=model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )
            
            # Parse the JSON response
            response_data = json.loads(response['body'].read())
            
            response_text = response_data['content'][0]['text']
            
            # Extract the first JSON-like structure
            json_text = extract_first_json(response_text)

            if json_text is None:
                raise ValueError("No JSON content found")

            # Parse the JSON string into a Python dictionary
            data = json.loads(json_text)

            # Get the value of the "tdc" key
            tdc = data.get("tdc", [])

            result = aggregate_tdc_items(tdc)

            return {
                'statusCode': 200,
                'body': result,
                'headers': {
                    'Content-Type': 'application/json',
                    'model used': model_id
                }
            }
        except json.JSONDecodeError as json_err:
            if response_text:
                error_message = f"JSON decoding error: {str(json_err)}\nResponse text: {response_text}"
            else:
                error_message = f"JSON decoding error: {str(json_err)}"
            print(error_message) # This will log the error in CloudWatch
        except Exception as e:
            if response_data:
                error_message = f"An error occurred: {str(e)}\nResponse data: {json.dumps(response_data, indent=2)}"
            else:
                error_message = f"An error occurred: {str(e)}"
            print(error_message)  # This will log the error in CloudWatch

    # If none of the models succeeded, return an error
    raise Exception("All models failed to generate output.")
