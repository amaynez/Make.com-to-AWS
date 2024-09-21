import re
import json

def trim_before_heading(text):
    match = re.search(r'<h[12]>', text, re.IGNORECASE)
    return text[match.start():] if match else text

def lambda_handler(event, context):
    blog_sections = []
    
    for section in event:
        body_content = json.loads(section.get('body', '{}'))
        blog_section = body_content.get('blog_section', '')
        blog_sections.append(trim_before_heading(blog_section))
    
    blog_post = '\n\n'.join(blog_sections).strip()
    blog_post = re.sub(r'<h1>.*?</h1>', '', blog_post, flags=re.IGNORECASE | re.DOTALL)

    return {
        'statusCode': 200,
        'body': json.dumps({'blog_post': blog_post})
    }

