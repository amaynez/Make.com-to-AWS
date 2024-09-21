import re
import json

def trim_before_heading(text):
    # Try to find <h1> first
    h1_match = re.search(r'<h1>', text, re.IGNORECASE)
    if h1_match:
        return text[h1_match.start():]
    
    # If <h1> is not found, look for <h2>
    h2_match = re.search(r'<h2>', text, re.IGNORECASE)
    if h2_match:
        return text[h2_match.start():]
    
    # If neither <h1> nor <h2> is found, return the original text
    return text

def lambda_handler(event, context):
    # The event will contain an array of all processed sections
    processed_sections = event
    
    blog_post = ""
    
    # Concatenate all processed sections
    for section in processed_sections:
        # Assuming each section is a dictionary with a 'body' key
        body_content = section.get('body', '{}')
        body_content_post = json.loads(body_content)
        blog_section = body_content_post.get('blog_section', '')
        blog_post += trim_before_heading(blog_section) + "\n\n"
    
    # Remove any extra newlines
    blog_post = blog_post.strip()
    
    # Remove all <h1> tags and their content
    blog_post = re.sub(r'<h1>.*?</h1>', '', blog_post, flags=re.IGNORECASE | re.DOTALL)
    

    print(blog_post)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'blog_post': blog_post
        })
    }

