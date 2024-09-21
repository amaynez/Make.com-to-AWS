import json
import os
import boto3

def aggregate_tdc_items(tdc):
    def recursive_aggregate(item, prefix=""):
        content = [prefix + item['titulo']]
        content.extend(recursive_aggregate(subtema, prefix + "  ") for subtema in item.get('sub-temas', []))
        return '\n'.join(content)

    return [recursive_aggregate(top_level_item) for top_level_item in tdc]

def extract_first_json(text):
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
    parsed_response = event["metaOut"]
    if parsed_response['statusCode'] != 200:
        raise Exception(f"Error: {parsed_response}")
    
    title = json.loads(parsed_response['body'])['title']
    user_prompt = os.environ['USER_PROMPT'].replace("#####", title)

    bedrock_runtime = boto3.client('bedrock-runtime')
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 32000,
        "messages": [{"role": "user", "content": [{"type": "text", "text": f"{os.environ['SYSTEM_PROMPT']}\n\n{user_prompt}"}]}]
    }

    for model_id in [os.environ[f'BEDROCK_MODEL_ID_{i}'] for i in range(1, 5)]:
        try:
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
