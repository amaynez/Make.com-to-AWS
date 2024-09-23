import re
import json

"""
This script is a Lambda function that concatenates multiple blog sections generated in HTML format into a single blog post.
It processes input from an event, which contains multiple sections of a blog post.
The script trims each section to start from the first heading, removes any H1 tags,
and combines all sections into a single coherent blog post.

Key features:
- Trims content before the first heading in each section
- Removes all H1 tags from the final blog post
- Concatenates all sections with proper spacing
- Returns the result as a JSON response
"""

def trim_before_heading(text):
    """
    Trims the text to start from the first <h1> or <h2> tag.
    
    Args:
    text (str): The input text to trim
    
    Returns:
    str: The trimmed text starting from the first heading, or the original text if no heading is found
    """
    match = re.search(r'<h[12]>', text, re.IGNORECASE)
    return text[match.start():] if match else text

def lambda_handler(event, context):
    """
    Main Lambda function handler.
    
    Args:
    event (list): List of dictionaries containing blog sections
    context: AWS Lambda context object (unused in this function)
    
    Returns:
    dict: A dictionary with statusCode and body containing the concatenated blog post
    """
    blog_sections = []
    
    # Process each section in the input event
    for section in event:
        body_content = json.loads(section.get('body', '{}'))
        blog_section = body_content.get('blog_section', '')
        blog_sections.append(trim_before_heading(blog_section))
    
    # Concatenate all blog sections with double newline separation
    blog_post = '\n\n'.join(blog_sections).strip()
    
    # Remove any H1 tags from the final blog post
    blog_post = re.sub(r'<h1>.*?</h1>', '', blog_post, flags=re.IGNORECASE | re.DOTALL)

    # Return the result as a JSON response
    return {
        'statusCode': 200,
        'body': json.dumps({'blog_post': blog_post})
    }

